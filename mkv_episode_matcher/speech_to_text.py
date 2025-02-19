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

def check_gpu_support():
    logger.info('Checking GPU support...')
    if torch.cuda.is_available():
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.warning("CUDA not available. Using CPU. Refer to https://pytorch.org/get-started/locally/ for GPU support.")