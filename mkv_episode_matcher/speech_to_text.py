# mkv_episode_matcher/speech_to_text.py

import os
import subprocess
from pathlib import Path
import whisper
import torch
from loguru import logger

def process_speech_to_text(mkv_file, output_dir):
    """
    Convert MKV file to transcript using Whisper.
    
    Args:
        mkv_file (str): Path to MKV file
        output_dir (str): Directory to save transcript files
    """
    # Extract audio if not already done
    wav_file = extract_audio(mkv_file, output_dir)
    if not wav_file:
        return None

    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("CUDA not available. Using CPU.")
    
    model = whisper.load_model("base", device=device)
    
    # Generate transcript
    segments_file = os.path.join(output_dir, f"{Path(mkv_file).stem}.segments.json")
    if not os.path.exists(segments_file):
        try:
            result = model.transcribe(
                wav_file,
                task="transcribe",
                language="en",
            )
            
            # Save segments
            import json
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump(result["segments"], f, indent=2)
                
            logger.info(f"Transcript saved to {segments_file}")
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None
    else:
        logger.info(f"Using existing transcript: {segments_file}")
    
    return segments_file

def extract_audio(mkv_file, output_dir):
    """
    Extract audio from MKV file using FFmpeg.
    
    Args:
        mkv_file (str): Path to MKV file
        output_dir (str): Directory to save WAV file
        
    Returns:
        str: Path to extracted WAV file
    """
    wav_file = os.path.join(output_dir, f"{Path(mkv_file).stem}.wav")
    
    if not os.path.exists(wav_file):
        logger.info(f"Extracting audio from {mkv_file}")
        try:
            cmd = [
                'ffmpeg',
                '-i', mkv_file,
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',  # Convert to PCM format
                '-ar', '16000',  # Set sample rate to 16kHz
                '-ac', '1',  # Convert to mono
                wav_file
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Audio extracted to {wav_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    else:
        logger.info(f"Audio file {wav_file} already exists, skipping extraction")
    
    return wav_file