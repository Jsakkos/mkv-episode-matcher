# whisper_transcriber.py
import os
import subprocess
import tempfile

import torch
import whisper
from loguru import logger


def check_cuda():
    """Check if CUDA is available and log device information."""
    if torch.cuda.is_available():
        logger.info(f'CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}')
        logger.debug(f'CUDA version: {torch.version.cuda}')
        logger.debug(f'PyTorch version: {torch.__version__}')
    else:
        logger.info('CUDA is not available. Using CPU.')


def extract_audio(mkv_file, output_dir):
    """
    Extract the first 5 minutes of English audio from an MKV file.

    Args:
        mkv_file (str): Path to the MKV file
        output_dir (str): Directory to save the audio file

    Returns:
        str: Path to the extracted audio file
    """
    base_name = os.path.splitext(os.path.basename(mkv_file))[0]
    audio_file = os.path.join(output_dir, f'{base_name}.wav')

    if not os.path.exists(audio_file):
        logger.info(f'Extracting audio from {mkv_file}')
        cmd = [
            'ffmpeg',
            '-i',
            mkv_file,
            '-t',
            '600',  # First 10 minutes
            '-map',
            '0:a:0',  # First audio track
            '-acodec',
            'pcm_s16le',
            '-ac',
            '1',  # Mono
            audio_file,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f'Audio extracted to {audio_file}')
        except subprocess.CalledProcessError as e:
            logger.error(f'Error extracting audio: {e}')
            return None
    else:
        logger.info(f'Audio file {audio_file} already exists')

    return audio_file


def transcribe_audio(audio_file, model_name='base.en'):
    """
    Transcribe audio using Whisper.

    Args:
        audio_file (str): Path to the audio file
        model_name (str): Name of the Whisper model to use

    Returns:
        str: Transcribed text
    """
    logger.info(f'Loading Whisper model: {model_name}')
    model = whisper.load_model(model_name)

    logger.info(f'Transcribing {audio_file}')
    try:
        result = model.transcribe(audio_file)
        return result['text']
    except Exception as e:
        logger.error(f'Error during transcription: {e}')
        return None


def convert_mkv_to_text(mkv_files, output_dir, model_name="base.en"):
    """
    Convert MKV files to text transcriptions using Whisper.
    
    Args:
        mkv_files (list): List of MKV files to process
        output_dir (str): Directory to save output files
        model_name (str): Name of the Whisper model to use
        
    Returns:
        dict: Dictionary mapping file paths to their transcriptions in a list format compatible with SRT structure
    """
    check_cuda()
    os.makedirs(output_dir, exist_ok=True)
    
    transcriptions = {}
    for mkv_file in mkv_files:
        base_name = os.path.splitext(os.path.basename(mkv_file))[0]
        text_file = os.path.join(output_dir, f"{base_name}.txt")
        
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            audio_file = extract_audio(mkv_file, output_dir)
            if audio_file:
                text = transcribe_audio(audio_file, model_name)
                if text:
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                os.remove(audio_file)  # Clean up audio file
        
        if text:
            # Convert text into a list format similar to SRT structure
            # Split into sentences and format like SRT lines
            sentences = text.replace('.', '.\n').replace('!', '!\n').replace('?', '?\n').split('\n')
            sentences = [s.strip() for s in sentences if s.strip()]
            # Store as list of lists to match SRT format
            transcriptions[text_file] = [[sentence] for sentence in sentences]
                
    return transcriptions
