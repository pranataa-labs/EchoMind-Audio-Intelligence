"""Audio processing utilities for EchoMind."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import soundfile as sf


class AudioProcessor:
    """Handles audio inspection, conversion, and temporary storage."""

    SUPPORTED_FORMATS = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"]

    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """Extract duration and audio properties safely."""
        info = {
            "duration": 0.0,
            "sample_rate": 16000,
            "channels": 1,
            "format": Path(file_path).suffix.lower(),
            "size_mb": os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0.0,
        }

        try:
            with sf.SoundFile(file_path) as s:
                info["duration"] = len(s) / s.samplerate
                info["sample_rate"] = s.samplerate
                info["channels"] = s.channels
        except Exception:
            # Fallback if soundfile doesn't directly support container (e.g. m4a/mp3)
            # Whisper handles mp3/m4a directly through av / ffmpeg
            pass

        return info

    @staticmethod
    def save_upload_to_temp(uploaded_file, suffix: str = ".wav") -> str:
        """Save a streamlit uploaded file buffer to a persistent temp file."""
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir)
        temp_file.write(uploaded_file.getbuffer() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read())
        temp_file.flush()
        temp_file.close()
        return temp_file.name
