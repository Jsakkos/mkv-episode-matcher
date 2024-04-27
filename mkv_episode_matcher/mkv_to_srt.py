import os
import subprocess
import sys

# Get the absolute path of the parent directory of the current script.
parent_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory to the Python path.
sys.path.append(parent_dir)
# Add the 'libraries' directory to the Python path.
sys.path.append(os.path.join(parent_dir, "libraries"))
# Add the 'libraries' directory to the Python path.
sys.path.append(os.path.join(parent_dir, "..", "libraries", "pgs2srt"))
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytesseract
from imagemaker import make_image
from loguru import logger
from pgsreader import PGSReader
from PIL import Image, ImageOps

from mkv_episode_matcher.__main__ import CONFIG_FILE
from mkv_episode_matcher.config import get_config


def convert_mkv_to_sup(mkv_file, output_dir):
    """
    Convert an .mkv file to a .sup file using FFmpeg and pgs2srt.

    Args:
        mkv_file (str): Path to the .mkv file.
        output_dir (str): Path to the directory where the .sup file will be saved.

    Returns:
        str: Path to the converted .sup file.
    """
    # Get the base name of the .mkv file without the extension
    base_name = os.path.splitext(os.path.basename(mkv_file))[0]

    # Construct the output .sup file path
    sup_file = os.path.join(output_dir, f"{base_name}.sup")
    if not os.path.exists(sup_file):
        logger.info(f"Processing {mkv_file} to {sup_file}")
        # FFmpeg command to convert .mkv to .sup
        ffmpeg_cmd = ["ffmpeg", "-i", mkv_file, "-map", "0:s:0", "-c", "copy", sup_file]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            logger.info(f"Converted {mkv_file} to {sup_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting {mkv_file}: {e}")
    else:
        logger.info(f"File {sup_file} already exists, skipping")
    return sup_file


@logger.catch
def perform_ocr(sup_file_path):
    """
    Perform OCR on a .sup file and save the extracted text to a .srt file.

    Args:
        sup_file_path (str): Path to the .sup file.
    """

    # Get the base name of the .sup file without the extension
    base_name = os.path.splitext(os.path.basename(sup_file_path))[0]
    output_dir = os.path.dirname(sup_file_path)
    logger.info(f"Performing OCR on {sup_file_path}")
    # Construct the output .srt file path
    srt_file = os.path.join(output_dir, f"{base_name}.srt")

    # Load a PGS/SUP file.
    pgs = PGSReader(sup_file_path)

    # Set index
    i = 0

    # Complete subtitle track index
    si = 0

    tesseract_lang = "eng"
    tesseract_config = f"-c tessedit_char_blacklist=[] --psm 6 --oem {1}"

    config = get_config(CONFIG_FILE)
    tesseract_path = config.get("tesseract_path")
    logger.debug(f"Setting Teesseract Path to {tesseract_path}")
    pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)

    # SubRip output
    output = ""

    if not os.path.exists(srt_file):
        # Iterate the pgs generator
        for ds in pgs.iter_displaysets():
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
        with open(srt_file, "w") as f:
            f.write(output)
        logger.info(f"Saved to: {srt_file}")


def convert_mkv_to_srt(season_path, mkv_files):
    """
    Converts MKV files to SRT format.

    Args:
        season_path (str): The path to the season directory.
        mkv_files (list): List of MKV files to convert.

    Returns:
        None
    """
    logger.info(f"Converting {len(mkv_files)} files to SRT")
    output_dir = os.path.join(season_path, "ocr")
    os.makedirs(output_dir, exist_ok=True)
    sup_files = []
    for mkv_file in mkv_files:
        sup_file = convert_mkv_to_sup(mkv_file, output_dir)
        sup_files.append(sup_file)
    with ThreadPoolExecutor() as executor:
        for sup_file in sup_files:
            executor.submit(perform_ocr, sup_file)
