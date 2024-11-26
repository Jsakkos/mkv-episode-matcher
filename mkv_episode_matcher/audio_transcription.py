from loguru import logger
import whisper
import os
import json
from concurrent.futures import ThreadPoolExecutor
import subprocess
from vosk import Model, KaldiRecognizer
import wave
def process_speech_to_text(mkv_files, output_dir, model_path):
    """
    Process multiple MKV files for speech recognition.
    
    Args:
        mkv_files (list): List of MKV file paths
        output_dir (str): Directory to save extracted audio and SRT files
        model_path (str): Path to the Vosk model directory
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # First extract all audio
    wav_files = []
    for mkv_file in mkv_files:
        wav_file = extract_audio(mkv_file, output_dir)
        if wav_file:
            wav_files.append(wav_file)
            
    # Process speech recognition in parallel
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(perform_speech_recognition, wav_file, model_path)
            for wav_file in wav_files
        ]
        
        # Wait for all recognition tasks to complete
        srt_files = []
        for future in futures:
            srt_file = future.result()
            if srt_file:
                srt_files.append(srt_file)
    
    return srt_files
def extract_audio(mkv_file, output_dir):
    """
    Extract audio from MKV file using FFmpeg.
    
    Args:
        mkv_file (str): Path to the MKV file
        output_dir (str): Directory to save the extracted audio
        
    Returns:
        str: Path to the extracted WAV file
    """
    base_name = os.path.splitext(os.path.basename(mkv_file))[0]
    wav_file = os.path.join(output_dir, f"{base_name}.wav")
    
    if not os.path.exists(wav_file):
        logger.info(f"Extracting audio from {mkv_file} to {wav_file}")
        # Extract audio stream and convert to WAV format
        ffmpeg_cmd = [
            "ffmpeg", "-i", mkv_file,
            "-vn",  # Disable video
            "-acodec", "pcm_s16le",  # Convert to PCM format
            "-ar", "16000",  # Set sample rate to 16kHz
            "-ac", "1",  # Convert to mono
            wav_file
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            logger.info(f"Audio extracted to {wav_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting audio from {mkv_file}: {e}")
            return None
    else:
        logger.info(f"Audio file {wav_file} already exists, skipping extraction")
    
    return wav_file
def perform_speech_recognition(wav_file, model_type="base"):
    """
    Perform speech recognition on a WAV file using Vosk.
    
    Args:
        wav_file (str): Path to the WAV file
        model_path (str): Path to the Vosk model directory
        
    Returns:
        str: Path to the generated SRT file
    """

    srt_file = wav_file.replace('.wav', '_speech.srt')
    
    if os.path.exists(srt_file):
        logger.info(f"SRT file {srt_file} already exists, skipping recognition")
        return srt_file
        
    try:
        model = whisper.load_model(model_type)
        
        with wave.open(wav_file, "rb") as wf:
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)  # Enable word timing
            
            srt_index = 1
            results = []
            
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get('result'):
                        results.append(result)
        
        # Process final result
        final = json.loads(rec.FinalResult())
        if final.get('result'):
            results.append(final)
            
        # Convert results to SRT format
        with open(srt_file, 'w', encoding='utf-8') as f:
            for result in results:
                if not result.get('result'):
                    continue
                    
                words = result['result']
                if not words:
                    continue
                
                # Group words into subtitle blocks (e.g., 5 seconds per block)
                block_duration = 5.0
                current_block = []
                current_start = words[0]['start']
                
                for word in words:
                    if word['end'] - current_start <= block_duration:
                        current_block.append(word['word'])
                    else:
                        # Write current block to SRT
                        end_time = min(current_start + block_duration, word['start'])
                        f.write(f"{srt_index}\n")
                        f.write(f"{format_timestamp(current_start)} --> {format_timestamp(end_time)}\n")
                        f.write(f"{' '.join(current_block)}\n\n")
                        
                        # Start new block
                        current_block = [word['word']]
                        current_start = word['start']
                        srt_index += 1
                
                # Write final block
                if current_block:
                    f.write(f"{srt_index}\n")
                    f.write(f"{format_timestamp(current_start)} --> {format_timestamp(words[-1]['end'])}\n")
                    f.write(f"{' '.join(current_block)}\n\n")
                    srt_index += 1
                    
        logger.info(f"Speech recognition completed. SRT saved to {srt_file}")
        return srt_file
        
    except Exception as e:
        logger.error(f"Error during speech recognition: {e}")
        return None

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"