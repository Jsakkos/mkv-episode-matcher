import os
import subprocess
import sys

# Get the absolute path of the parent directory of the current script.
parent_dir = os.path.dirname(os.path.abspath(__file__))
# Add the 'pgs2srt' directory to the Python path.
sys.path.append(os.path.join(parent_dir, "libraries", "pgs2srt"))
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
import pytesseract
from imagemaker import make_image
from loguru import logger
from pgsreader import PGSReader
from PIL import Image, ImageOps
from typing import Optional
from mkv_episode_matcher.__main__ import CONFIG_FILE
from mkv_episode_matcher.config import get_config
def check_if_processed(filename: str) -> bool:
    """
    Check if the file has already been processed (has SxxExx format)
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: True if file is already processed
    """
    import re
    match = re.search(r"S\d+E\d+", filename)
    return bool(match)


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
def perform_ocr(sup_file_path: str) -> Optional[str]:
    """
    Perform OCR on a .sup file and save the extracted text to a .srt file.
    Returns the path to the created SRT file.
    """
    # Get the base name of the .sup file without the extension
    base_name = os.path.splitext(os.path.basename(sup_file_path))[0]
    output_dir = os.path.dirname(sup_file_path)
    logger.info(f"Performing OCR on {sup_file_path}")
    
    # Construct the output .srt file path
    srt_file = os.path.join(output_dir, f"{base_name}.srt")

    if os.path.exists(srt_file):
        logger.info(f"SRT file {srt_file} already exists, skipping OCR")
        return srt_file

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


# def convert_mkv_to_srt(season_path, mkv_files):
#     """
#     Converts MKV files to SRT format.

#     Args:
#         season_path (str): The path to the season directory.
#         mkv_files (list): List of MKV files to convert.

#     Returns:
#         None
#     """
#     logger.info(f"Converting {len(mkv_files)} files to SRT")
#     output_dir = os.path.join(season_path, "ocr")
#     os.makedirs(output_dir, exist_ok=True)
#     sup_files = []
#     for mkv_file in mkv_files:
#         sup_file = convert_mkv_to_sup(mkv_file, output_dir)
#         sup_files.append(sup_file)
#     with ThreadPoolExecutor() as executor:
#         for sup_file in sup_files:
#             executor.submit(perform_ocr, sup_file)

        

def extract_subtitles(mkv_file: str, output_dir: str) -> Optional[str]:
    """
    Extract subtitles from MKV file based on detected subtitle type.
    """
    subtitle_type, stream_index = detect_subtitle_type(mkv_file)
    if not subtitle_type:
        logger.error(f"No supported subtitle streams found in {mkv_file}")
        return None
        
    base_name = Path(mkv_file).stem
    
    if subtitle_type == 'subrip':
        # For SRT subtitles, extract directly to .srt
        output_file = os.path.join(output_dir, f"{base_name}.srt")
        if not os.path.exists(output_file):
            cmd = [
                "ffmpeg", "-i", mkv_file,
                "-map", f"0:{stream_index}",
                output_file
            ]
    else:
        # For DVD or PGS subtitles, extract to SUP format first
        output_file = os.path.join(output_dir, f"{base_name}.sup")
        if not os.path.exists(output_file):
            cmd = [
                "ffmpeg", "-i", mkv_file,
                "-map", f"0:{stream_index}",
                "-c", "copy",
                output_file
            ]
    
    if not os.path.exists(output_file):
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Extracted subtitles from {mkv_file} to {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting subtitles: {e}")
            return None
    else:
        logger.info(f"Subtitle file {output_file} already exists, skipping extraction")
        return output_file

def convert_mkv_to_srt(season_path: str, mkv_files: list[str]) -> None:
    """
    Convert subtitles from MKV files to SRT format.
    """
    logger.info(f"Converting {len(mkv_files)} files to SRT")
    
    # Filter out already processed files
    unprocessed_files = []
    for mkv_file in mkv_files:
        if check_if_processed(os.path.basename(mkv_file)):
            logger.info(f"Skipping {mkv_file} - already processed")
            continue
        unprocessed_files.append(mkv_file)
    
    if not unprocessed_files:
        logger.info("No new files to process")
        return
        
    # Create OCR directory
    output_dir = os.path.join(season_path, "ocr")
    os.makedirs(output_dir, exist_ok=True)
    
    for mkv_file in unprocessed_files:
        subtitle_file = extract_subtitles(mkv_file, output_dir)
        if not subtitle_file:
            continue
            
        if subtitle_file.endswith('.srt'):
            # Already have SRT, keep it in OCR directory
            logger.info(f"Extracted SRT subtitle to {subtitle_file}")
        else:
            # For SUP files (DVD or PGS), perform OCR
            srt_file = perform_ocr(subtitle_file)
            if srt_file:
                logger.info(f"Created SRT from OCR: {srt_file}")
            
def detect_subtitle_type(mkv_file: str) -> tuple[Optional[str], Optional[int]]:
    """
    Detect the type and index of subtitle streams in an MKV file.
    """
    cmd = ["ffmpeg", "-i", mkv_file]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        subtitle_streams = []
        for line in result.stderr.split('\n'):
            if 'Subtitle' in line:
                stream_index = int(line.split('#0:')[1].split('(')[0])
                if 'subrip' in line:
                    subtitle_streams.append(('subrip', stream_index))
                elif 'dvd_subtitle' in line:
                    subtitle_streams.append(('dvd_subtitle', stream_index))
                elif 'hdmv_pgs_subtitle' in line:
                    subtitle_streams.append(('hdmv_pgs_subtitle', stream_index))
        
        # Prioritize subtitle formats: SRT > DVD > PGS
        for format_priority in ['subrip', 'dvd_subtitle', 'hdmv_pgs_subtitle']:
            for format_type, index in subtitle_streams:
                if format_type == format_priority:
                    return format_type, index
                    
        return None, None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error detecting subtitle type: {e}")
        return None, None