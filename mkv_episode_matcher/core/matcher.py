import tempfile
from collections import Counter
from pathlib import Path

from loguru import logger

from mkv_episode_matcher.core.models import MatchCandidate, MatchResult, SubtitleFile
from mkv_episode_matcher.core.providers.asr import ASRProvider
from mkv_episode_matcher.core.utils import (
    SubtitleReader,
    clean_text,
    extract_audio_chunk,
    get_video_duration,
)


class MultiSegmentMatcher:
    def __init__(self, asr_provider: ASRProvider, temp_dir: Path | None = None):
        self.asr = asr_provider
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "mkv_matcher_chunks"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.chunk_duration = 30
        self.min_confidence = 0.6

    def _process_chunk(
        self, video_path: Path, start_time: float, reference_subs: list[SubtitleFile]
    ) -> list[MatchCandidate]:
        """Process a single chunk: Extract -> Transcribe -> Match against all subs."""
        chunk_path = self.temp_dir / f"{video_path.stem}_{start_time}.wav"
        try:
            extract_audio_chunk(video_path, start_time, self.chunk_duration, chunk_path)
            transcription = self.asr.transcribe(chunk_path)

            # Clean transcription
            clean_trans = clean_text(transcription)
            if len(clean_trans) < 10:
                logger.debug(f"Transcription too short at {start_time}s: {clean_trans}")
                return []

            candidates = []
            for sub in reference_subs:
                # Load text for this time window
                # Note: SubtitleReader.extract_chunk reads file every time.
                # Optimization: Cache full subtitle content in memory for the session?
                # For now, rely on OS file caching.
                if not sub.content:
                    sub.content = SubtitleReader.read_srt_file(sub.path)

                ref_text = " ".join(
                    SubtitleReader.extract_subtitle_chunk(
                        sub.content, start_time, start_time + self.chunk_duration
                    )
                )
                ref_text = clean_text(ref_text)

                if not ref_text:
                    continue

                score = self.asr.calculate_match_score(clean_trans, ref_text)
                if score > self.min_confidence:
                    candidates.append(
                        MatchCandidate(
                            episode_info=sub.episode_info,
                            confidence=score,
                            reference_file=sub.path,
                        )
                    )

            return candidates

        except Exception as e:
            logger.error(f"Error processing chunk at {start_time}: {e}")
            return []
        finally:
            if chunk_path.exists():
                chunk_path.unlink()

    def match(
        self, video_path: Path, reference_subs: list[SubtitleFile]
    ) -> MatchResult | None:
        duration = get_video_duration(video_path)
        if duration < 60:
            logger.warning(f"Video too short: {duration}s")
            return None

        # Strategy: 3 primary checkpoints with fallbacks for empty segments
        # Avoid intro (0-120s usually).
        # Primary checkpoints: 15% (after intro), 50% (middle), 85% (end).
        primary_checkpoints = [duration * 0.15, duration * 0.50, duration * 0.85]

        # Fallback checkpoints for when primary segments fail
        fallback_checkpoints = [
            duration * 0.25,
            duration * 0.35,
            duration * 0.65,
            duration * 0.75,
        ]

        # Combine and filter checkpoints
        all_checkpoints = primary_checkpoints + fallback_checkpoints
        checkpoints = [t for t in all_checkpoints if t < duration - 10]

        # Limit total attempts to prevent excessive processing
        checkpoints = checkpoints[:6]

        # Parallel processing of chunks?
        # ASR might be GPU bound and not parallelizable easily within one process due to GIL/VRAM.
        # But extraction is CPU/IO.
        # We'll do sequential for now to be safe with VRAM users.
        # "Faster-Whisper" releases GIL mostly, but VRAM contention is real.

        all_candidates: list[MatchCandidate] = []
        successful_segments = 0
        empty_segments = 0

        for i, t in enumerate(checkpoints):
            logger.info(f"Checking segment {i + 1}/{len(checkpoints)} at {t:.1f}s")

            candidates = self._process_chunk(video_path, t, reference_subs)

            if not candidates:
                empty_segments += 1
                logger.debug(f"Empty transcription at {t:.1f}s (segment {i + 1})")
                # Continue trying more segments if we're still in primary checkpoints
                # or if we haven't found any successful matches yet
                if i < 3 or successful_segments == 0:
                    continue
                else:
                    # We have some matches already and this is a fallback segment
                    break

            successful_segments += 1
            # Sort candidates by score
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            top_match = candidates[0]

            logger.debug(
                f"Top match at {t}s: {top_match.episode_info.s_e_format} ({top_match.confidence:.2f})"
            )

            # FAIL FAST: If we have an Extremely High confidence Unique match
            # and it's not from the very first segment (which might be intro)
            if (
                i > 0 and top_match.confidence > 0.92
            ):  # Not first segment, very high score
                # Check for ambiguity
                if len(candidates) > 1 and candidates[1].confidence > 0.8:
                    logger.debug("Ambiguous high score, continuing...")
                else:
                    logger.info("Found definitive match, skipping remaining chunks.")
                    return MatchResult(
                        episode_info=top_match.episode_info,
                        confidence=top_match.confidence,
                        matched_file=video_path,
                        matched_time=t,
                        chunk_index=i,
                        model_name="unknown",
                        original_file=video_path,
                    )

            all_candidates.extend(candidates)

        logger.info(
            f"Processed {successful_segments} successful segments, {empty_segments} empty segments"
        )

        # Voting Logic
        if not all_candidates:
            return None

        # Group by Episode ID (SxxExx)
        vote_counter = Counter()
        score_sum = {}

        for c in all_candidates:
            key = c.episode_info.s_e_format
            vote_counter[key] += 1
            if key not in score_sum:
                score_sum[key] = 0.0
            score_sum[key] += c.confidence

        # Winner is the one with most votes. Tie-break with avg confidence.
        best_ep = None
        max_votes = 0

        for ep_key, votes in vote_counter.items():
            if votes > max_votes:
                max_votes = votes
                best_ep = ep_key
            elif votes == max_votes:
                # Tie break
                if best_ep and score_sum[ep_key] > score_sum[best_ep]:
                    best_ep = ep_key

        if best_ep:
            # Reconstruct result based on the episode key
            # Find a candidate that matches this key to get details
            # Ideally return the one with highest confidence
            winning_candidates = [
                c for c in all_candidates if c.episode_info.s_e_format == best_ep
            ]
            best_candidate = max(winning_candidates, key=lambda c: c.confidence)

            return MatchResult(
                episode_info=best_candidate.episode_info,
                confidence=best_candidate.confidence,
                matched_file=video_path,
                matched_time=0,
                chunk_index=-1,  # Consensus
                model_name="consensus",
                original_file=video_path,
            )

        return None
