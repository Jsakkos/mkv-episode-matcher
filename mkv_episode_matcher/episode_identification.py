import json
import os
import subprocess
import tempfile
from pathlib import Path
import torch
from rapidfuzz import fuzz
from loguru import logger
import whisper
import numpy as np
import re
from pathlib import Path
import chardet
from loguru import logger

class EpisodeMatcher:
    def __init__(self, cache_dir, show_name, min_confidence=0.6):
        self.cache_dir = Path(cache_dir)
        self.min_confidence = min_confidence
        self.show_name = show_name
        self.chunk_duration = 300  # 5 minutes
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.temp_dir = Path(tempfile.gettempdir()) / "whisper_chunks"
        self.temp_dir.mkdir(exist_ok=True)
        
    def clean_text(self, text):
        text = text.lower().strip()
        text = re.sub(r'\[.*?\]|\<.*?\>', '', text)
        text = re.sub(r'([A-Za-z])-\1+', r'\1', text)
        return ' '.join(text.split())

    def chunk_score(self, whisper_chunk, ref_chunk):
        whisper_clean = self.clean_text(whisper_chunk)
        ref_clean = self.clean_text(ref_chunk)
        return (fuzz.token_sort_ratio(whisper_clean, ref_clean) * 0.7 + 
                fuzz.partial_ratio(whisper_clean, ref_clean) * 0.3) / 100.0

    def extract_audio_chunk(self, mkv_file, start_time):
        """Extract a chunk of audio from MKV file."""
        chunk_path = self.temp_dir / f"chunk_{start_time}.wav"
        if not chunk_path.exists():
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-t', str(self.chunk_duration),
                '-i', mkv_file,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                str(chunk_path)
            ]
            subprocess.run(cmd, capture_output=True)
        return str(chunk_path)

    def load_reference_chunk(self, srt_file, chunk_idx):
        """
        Load reference subtitles for a specific time chunk with robust encoding handling.
        
        Args:
            srt_file (str or Path): Path to the SRT file
            chunk_idx (int): Index of the chunk to load
            
        Returns:
            str: Combined text from the subtitle chunk
        """
        chunk_start = chunk_idx * self.chunk_duration
        chunk_end = chunk_start + self.chunk_duration
        
        try:
            # Read the file content using our robust reader
            reader = SubtitleReader()
            content = reader.read_srt_file(srt_file)
            
            # Extract subtitles for the time chunk
            text_lines = reader.extract_subtitle_chunk(content, chunk_start, chunk_end)
            
            return ' '.join(text_lines)
            
        except Exception as e:
            logger.error(f"Error loading reference chunk from {srt_file}: {e}")
            return ''

    def identify_episode(self, video_file, temp_dir, season_number):
        try:
            # Get video duration
            duration = float(subprocess.check_output([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_file
            ]).decode())
            
            total_chunks = int(np.ceil(duration / self.chunk_duration))
            
            # Load Whisper model
            model = whisper.load_model("base", device=self.device)
            
            # Get season-specific reference files using multiple patterns
            reference_dir = self.cache_dir / "data" / self.show_name
            
            # Create season patterns for different formats
            patterns = [
                f"S{season_number:02d}E",  # S01E01
                f"S{season_number}E",      # S1E01
                f"{season_number:02d}x",   # 01x01
                f"{season_number}x",       # 1x01
            ]
            
            reference_files = []
            for pattern in patterns:
                files = [f for f in reference_dir.glob("*.srt") 
                        if any(re.search(f"{p}\\d+", f.name, re.IGNORECASE) 
                        for p in patterns)]
                reference_files.extend(files)
            
            # Remove duplicates while preserving order
            reference_files = list(dict.fromkeys(reference_files))
            
            if not reference_files:
                logger.error(f"No reference files found for season {season_number}")
                return None
                
            # Process chunks until match found
            for chunk_idx in range(min(3, total_chunks)):  # Only try first 3 chunks
                start_time = chunk_idx * self.chunk_duration
                audio_path = self.extract_audio_chunk(video_file, start_time)
                
                # Transcribe chunk
                result = model.transcribe(
                    audio_path,
                    task="transcribe",
                    language="en"
                )
                
                chunk_text = result["text"]
                best_confidence = 0
                best_match = None
                
                # Compare with reference chunks
                for ref_file in reference_files:
                    ref_text = self.load_reference_chunk(ref_file, chunk_idx)
                    confidence = self.chunk_score(chunk_text, ref_text)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = ref_file
                        
                    if confidence > self.min_confidence:
                        season_ep = re.search(r'S(\d+)E(\d+)', best_match.stem)
                        if season_ep:
                            season, episode = map(int, season_ep.groups())
                            return {
                                'season': season,
                                'episode': episode,
                                'confidence': best_confidence,
                                'reference_file': str(best_match),
                            }
            
            return None
            
        finally:
            # Cleanup temp files
            for file in self.temp_dir.glob("chunk_*.wav"):
                file.unlink()

def detect_file_encoding(file_path):
    """
    Detect the encoding of a file using chardet.
    
    Args:
        file_path (str or Path): Path to the file
        
    Returns:
        str: Detected encoding, defaults to 'utf-8' if detection fails
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        
        logger.debug(f"Detected encoding {encoding} with {confidence:.2%} confidence for {file_path}")
        return encoding if encoding else 'utf-8'
    except Exception as e:
        logger.warning(f"Error detecting encoding for {file_path}: {e}")
        return 'utf-8'

def read_file_with_fallback(file_path, encodings=None):
    """
    Read a file trying multiple encodings in order of preference.
    
    Args:
        file_path (str or Path): Path to the file
        encodings (list): List of encodings to try, defaults to common subtitle encodings
        
    Returns:
        str: File contents
        
    Raises:
        ValueError: If file cannot be read with any encoding
    """
    if encodings is None:
        # First try detected encoding, then fallback to common subtitle encodings
        detected = detect_file_encoding(file_path)
        encodings = [detected, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    file_path = Path(file_path)
    errors = []
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {file_path} using {encoding} encoding")
            return content
        except UnicodeDecodeError as e:
            errors.append(f"{encoding}: {str(e)}")
            continue
            
    error_msg = f"Failed to read {file_path} with any encoding. Errors:\n" + "\n".join(errors)
    logger.error(error_msg)
    raise ValueError(error_msg)

class SubtitleReader:
    """Helper class for reading and parsing subtitle files."""
    
    @staticmethod
    def parse_timestamp(timestamp):
        """Parse SRT timestamp into seconds."""
        hours, minutes, seconds = timestamp.replace(',', '.').split(':')
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    
    @staticmethod
    def read_srt_file(file_path):
        """
        Read an SRT file and return its contents with robust encoding handling.
        
        Args:
            file_path (str or Path): Path to the SRT file
            
        Returns:
            str: Contents of the SRT file
        """
        return read_file_with_fallback(file_path)
    
    @staticmethod
    def extract_subtitle_chunk(content, start_time, end_time):
        """
        Extract subtitle text for a specific time window.
        
        Args:
            content (str): Full SRT file content
            start_time (float): Chunk start time in seconds
            end_time (float): Chunk end time in seconds
            
        Returns:
            list: List of subtitle texts within the time window
        """
        text_lines = []
        
        for block in content.strip().split('\n\n'):
            lines = block.split('\n')
            if len(lines) < 3 or '-->' not in lines[1]:
                continue
                
            try:
                timestamp = lines[1]
                text = ' '.join(lines[2:])
                
                end_stamp = timestamp.split(' --> ')[1].strip()
                total_seconds = SubtitleReader.parse_timestamp(end_stamp)
                
                if start_time <= total_seconds <= end_time:
                    text_lines.append(text)
                    
            except (IndexError, ValueError) as e:
                logger.warning(f"Error parsing subtitle block: {e}")
                continue
                
        return text_lines