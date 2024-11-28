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
        """Load reference subtitles for a specific time chunk."""
        chunk_start = chunk_idx * self.chunk_duration
        chunk_end = chunk_start + self.chunk_duration
        text_lines = []
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        for block in content.split('\n\n'):
            lines = block.split('\n')
            if len(lines) < 3 or '-->' not in lines[1]:  # Skip malformed blocks
                continue
                
            try:
                timestamp = lines[1]
                text = ' '.join(lines[2:])
                
                end_time = timestamp.split(' --> ')[1].strip()
                hours, minutes, seconds = map(float, end_time.replace(',','.').split(':'))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                if chunk_start <= total_seconds <= chunk_end:
                    text_lines.append(text)
                    
            except (IndexError, ValueError):
                continue
                
        return ' '.join(text_lines)

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
            
            # Get season-specific reference files
            reference_dir = self.cache_dir / "data" / self.show_name
            season_pattern = f"S{season_number:02d}E"
            reference_files = [
                f for f in reference_dir.glob("*.srt")
                if season_pattern in f.name
            ]
            
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