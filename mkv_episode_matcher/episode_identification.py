# mkv_episode_matcher/episode_identification.py

import os
import glob
from pathlib import Path
from rapidfuzz import fuzz
from collections import defaultdict
import re
from loguru import logger
import json
import shutil

class EpisodeMatcher:
    def __init__(self, cache_dir, show_name,min_confidence=0.6):
        self.cache_dir = Path(cache_dir)
        self.min_confidence = min_confidence
        self.whisper_segments = None
        self.series_name = show_name
        
    def clean_text(self, text):
        """Clean text by removing stage directions and normalizing repeated words."""
        # Remove stage directions like [groans] and <i>SHIP:</i>
        text = re.sub(r'\[.*?\]|\<.*?\>', '', text)
        # Remove repeated words with dashes (e.g., "Y-y-you" -> "you")
        text = re.sub(r'([A-Za-z])-\1+', r'\1', text)
        # Remove multiple spaces
        text = ' '.join(text.split())
        return text.lower()

    def chunk_score(self, whisper_chunk, ref_chunk):
        """Calculate fuzzy match score between two chunks of text."""
        whisper_clean = self.clean_text(whisper_chunk)
        ref_clean = self.clean_text(ref_chunk)
        
        # Use token sort ratio to handle word order differences
        token_sort = fuzz.token_sort_ratio(whisper_clean, ref_clean)
        # Use partial ratio to catch substring matches
        partial = fuzz.partial_ratio(whisper_clean, ref_clean)
        
        # Weight token sort more heavily but consider partial matches
        return (token_sort * 0.7 + partial * 0.3) / 100.0

    def identify_episode(self, video_file, temp_dir):
        """Identify which episode matches this video file."""
        
        # Get series name from parent directory
        self.series_name = Path(video_file).parent.parent.name
        
        # Load whisper transcript if not already processed
        segments_file = Path(temp_dir) / f"{Path(video_file).stem}.segments.json"
        if not segments_file.exists():
            logger.error(f"No transcript found for {video_file}. Run speech recognition first.")
            return None
            
        with open(segments_file) as f:
            self.whisper_segments = json.load(f)

        # Get reference directory for this series
        reference_dir = self.cache_dir / "data" / self.series_name
        if not reference_dir.exists():
            logger.error(f"No reference files found for {self.series_name}")
            return None

        # Match against reference files
        match = self.match_all_references(reference_dir)
        
        if match and match['confidence'] >= self.min_confidence:
            # Extract season and episode from filename
            match_file = Path(match['file'])
            season_ep = re.search(r'S(\d+)E(\d+)', match_file.stem)
            if season_ep:
                season, episode = map(int, season_ep.groups())
                return {
                    'season': season,
                    'episode': episode,
                    'confidence': match['confidence'],
                    'reference_file': str(match_file),
                    'chunk_scores': match['chunk_scores']
                }
        
        return None

    def match_all_references(self, reference_dir):
        """Process all reference files and track matching scores."""
        results = defaultdict(list)
        best_match = None
        best_confidence = 0
        
        def process_chunks(ref_segments, filename):
            nonlocal best_match, best_confidence
            
            chunk_size = 300  # 5 minute chunks
            whisper_chunks = defaultdict(list)
            ref_chunks = defaultdict(list)
            
            # Group segments into time chunks
            for seg in self.whisper_segments:
                chunk_idx = int(float(seg['start']) // chunk_size)
                whisper_chunks[chunk_idx].append(seg['text'])
                
            for seg in ref_segments:
                chunk_idx = int(seg['start'] // chunk_size)
                ref_chunks[chunk_idx].append(seg['text'])
            
            # Score each chunk
            for chunk_idx in whisper_chunks:
                whisper_text = ' '.join(whisper_chunks[chunk_idx])
                
                # Look for matching reference chunk and adjacent chunks
                scores = []
                for ref_idx in range(max(0, chunk_idx-1), chunk_idx+2):
                    if ref_idx in ref_chunks:
                        ref_text = ' '.join(ref_chunks[ref_idx])
                        score = self.chunk_score(whisper_text, ref_text)
                        scores.append(score)
                
                if scores:
                    chunk_confidence = max(scores)
                    logger.info(f"File: {filename}, "
                              f"Time: {chunk_idx*chunk_size}-{(chunk_idx+1)*chunk_size}s, "
                              f"Confidence: {chunk_confidence:.2f}")
                    
                    results[filename].append({
                        'chunk_idx': chunk_idx,
                        'confidence': chunk_confidence
                    })
                    
                    # Early exit if we find a very good match
                    if chunk_confidence > self.min_confidence:
                        chunk_scores = results[filename]
                        confidence = sum(c['confidence'] * (0.9 ** c['chunk_idx']) 
                                      for c in chunk_scores) / len(chunk_scores)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                'file': filename,
                                'confidence': confidence,
                                'chunk_scores': chunk_scores
                            }
                        return True
                        
            return False

        # Process each reference file
        for ref_file in glob.glob(os.path.join(reference_dir, "*.srt")):
            ref_segments = self.parse_srt_to_segments(ref_file)
            filename = os.path.basename(ref_file)
            
            if process_chunks(ref_segments, filename):
                break

        # If no early match found, find best overall match
        if not best_match:
            for filename, chunks in results.items():
                # Weight earlier chunks more heavily
                confidence = sum(c['confidence'] * (0.9 ** c['chunk_idx']) 
                               for c in chunks) / len(chunks)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        'file': filename,
                        'confidence': confidence,
                        'chunk_scores': chunks
                    }
        
        return best_match

    def parse_srt_to_segments(self, srt_file):
        """Parse SRT file into list of segments with start/end times and text."""
        segments = []
        current_segment = {}
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.isdigit():  # Index
                if current_segment:
                    segments.append(current_segment)
                current_segment = {}
                
            elif '-->' in line:  # Timestamp
                start, end = line.split(' --> ')
                current_segment['start'] = self.timestr_to_seconds(start)
                current_segment['end'] = self.timestr_to_seconds(end)
                
            elif line:  # Text
                if 'text' in current_segment:
                    current_segment['text'] += ' ' + line
                else:
                    current_segment['text'] = line
                    
            i += 1
            
        if current_segment:
            segments.append(current_segment)
            
        return segments

    def timestr_to_seconds(self, timestr):
        """Convert SRT timestamp to seconds."""
        h, m, s = timestr.replace(',','.').split(':')
        return float(h) * 3600 + float(m) * 60 + float(s)