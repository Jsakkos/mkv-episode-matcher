#!/usr/bin/env python3

import argparse
import re
from datetime import datetime, timedelta

import pytesseract
from imagemaker import make_image
from Libraries.SubZero.post_processing import CommonFixes, FixOCR
from pgsreader import PGSReader
from PIL import Image, ImageOps

parser = argparse.ArgumentParser(description="Convert PGS subtitles to SubRip format.")

parser.add_argument("input", type=str, help="The input file (a .sup file).")
parser.add_argument("--output", type=str, help="The output file (a .srt file).")
parser.add_argument(
    "--oem",
    type=int,
    help="The OCR Engine Mode to use (Default: 1).",
    default=1,
    choices=range(4),
)
parser.add_argument(
    "--language", type=str, help="The language to use (Default: eng).", default="eng"
)
parser.add_argument(
    "--fix_common",
    help="Fixes common whitespace/punctuation issues.",
    dest="fix_common",
    action="store_true",
)
parser.add_argument(
    "--fix_common_ocr",
    help="Fixes common OCR issues for supported languages.",
    dest="fix_ocr",
    action="store_true",
)

args = parser.parse_args()

assert args.input is not None

# Unescape escaped spaces
file = args.input.replace("\\ ", " ")

print(f"Parsing: {file}")

# Load a PGS/SUP file.
pgs = PGSReader(file)

# Set index
i = 0

# Complete subtitle track index
si = 0

tesseract_lang = args.language
tesseract_config = f"-c tessedit_char_blacklist=[] --psm 6 --oem {args.oem}"

# If an output file for the subrip output is provided, use that.
# Otherwise remove the ".sup" extension from the input and append
# ".srt".
output_file = (
    args.output
    if args.output is not None
    else (args.input.replace(".sup", "") + ".srt")
)

# SubRip output
output = ""

fix_common = CommonFixes() if args.fix_common else None
fix_ocr = FixOCR(args.language) if args.fix_ocr else None

# Iterate the pgs generator
for ds in pgs.iter_displaysets():
    try:
        # If set has image, parse the image
        if ds.has_image:
            # Get Palette Display Segment
            pds = ds.pds[0]
            # Get Object Display Segment
            ods = ds.ods[0]

            if pds and ods:
                # Create and show the bitmap image and convert it to RGBA
                src = make_image(ods, pds).convert("RGBA")

                # Create grayscale image with black background
                img = Image.new("L", src.size, "BLACK")
                # Paste the subtitle bitmap
                img.paste(src, (0, 0), src)
                # Invert images so the text is readable by Tesseract
                img = ImageOps.invert(img)

                # Parse the image with tesesract
                text = pytesseract.image_to_string(
                    img, lang=tesseract_lang, config=tesseract_config
                ).strip()

                # Replace "|" with "I"
                # Works better than blacklisting "|" in Tesseract,
                # which results in I becoming "!" "i" and "1"
                text = re.sub(r"[|/\\]", "I", text)
                text = re.sub(r"[_]", "L", text)

                if args.fix_common:
                    text = fix_common.process(text)
                if args.fix_ocr:
                    text = fix_ocr.modify(text)

                start = datetime.fromtimestamp(ods.presentation_timestamp / 1000)
                start = start + timedelta(hours=-1)

        else:
            # Get Presentation Composition Segment
            pcs = ds.pcs[0]

            if pcs:
                end = datetime.fromtimestamp(pcs.presentation_timestamp / 1000)
                end = end + timedelta(hours=-1)

                if (
                    isinstance(start, datetime)
                    and isinstance(end, datetime)
                    and len(text)
                ):
                    si = si + 1
                    sub_output = str(si) + "\n"
                    sub_output += (
                        start.strftime("%H:%M:%S,%f")[0:12]
                        + " --> "
                        + end.strftime("%H:%M:%S,%f")[0:12]
                        + "\n"
                    )
                    sub_output += text + "\n\n"

                    output += sub_output
                    start = end = text = None
        i = i + 1

    except Exception as e:
        print(e)
        exit(1)

f = open(output_file, "w")
f.write(output)
f.close()
print(f"Saved to: {output_file}")
