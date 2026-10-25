"""Speech-to-Text Transcriber using faster-whisper with INT8 CPU optimization."""

import logging
from typing import Optional, Callable
from echomind.schemas import TranscriptResult, TranscriptSegment
from echomind.config import DEFAULT_WHISPER_MODEL, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE

logger = logging.getLogger(__name__)

# Cache models in memory to avoid reloading on every request
_MODEL_CACHE = {}


def get_whisper_model(model_size: str = DEFAULT_WHISPER_MODEL, device: str = DEFAULT_DEVICE, compute_type: str = DEFAULT_COMPUTE_TYPE):
    """Load or retrieve cached faster-whisper model."""
    key = f"{model_size}_{device}_{compute_type}"
    if key not in _MODEL_CACHE:
        from faster_whisper import WhisperModel
        logger.info(f"Loading faster-whisper model '{model_size}' on {device} ({compute_type})...")
        _MODEL_CACHE[key] = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _MODEL_CACHE[key]


class AudioTranscriber:
    """Handles fast speech-to-text transcription with timestamped segmentation."""

    def __init__(self, model_size: str = DEFAULT_WHISPER_MODEL, device: str = DEFAULT_DEVICE, compute_type: str = DEFAULT_COMPUTE_TYPE):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        num_speakers: int = 2
    ) -> TranscriptResult:
        """Transcribe an audio file into timestamped segments with speaker turns."""
        model = get_whisper_model(self.model_size, self.device, self.compute_type)

        if progress_callback:
            progress_callback(0.1, "Memuat model dan menganalisis audio...")

        # faster-whisper transcription
        segments_gen, info = model.transcribe(
            audio_path,
            language=language if language and language != "auto" else None,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            beam_size=5
        )

        detected_lang = info.language
        lang_prob = info.language_probability
        duration = info.duration

        if progress_callback:
            progress_callback(0.3, f"Bahasa terdeteksi: {detected_lang.upper()} ({lang_prob:.0%}). Melakukan transkripsi...")

        segments = []
        full_text_parts = []
        current_speaker_idx = 1
        last_end_time = 0.0

        for i, seg in enumerate(segments_gen):
            text = seg.text.strip()
            if not text:
                continue

            # Heuristic for speaker change: significant pause (> 1.6s) indicates possible speaker switch
            if last_end_time > 0 and (seg.start - last_end_time) > 1.6 and num_speakers > 1:
                current_speaker_idx = (current_speaker_idx % num_speakers) + 1

            speaker_name = f"Speaker {current_speaker_idx}"
            last_end_time = seg.end

            segment_obj = TranscriptSegment(
                id=i + 1,
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                speaker=speaker_name,
                text=text
            )
            segments.append(segment_obj)
            full_text_parts.append(f"[{speaker_name}] ({round(seg.start, 1)}s - {round(seg.end, 1)}s): {text}")

            if progress_callback and duration > 0:
                pct = min(0.3 + (seg.end / duration) * 0.6, 0.9)
                progress_callback(pct, f"Mentranskrip detik {int(seg.end)} dari {int(duration)}...")

        if progress_callback:
            progress_callback(1.0, "Transkripsi selesai!")

        return TranscriptResult(
            segments=segments,
            full_text="\n".join(full_text_parts),
            language=detected_lang,
            language_probability=round(lang_prob, 3),
            duration_seconds=round(duration, 2)
        )
