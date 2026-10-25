"""Audio processing utilities for EchoMind."""

import os
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import soundfile as sf
import av


class AudioProcessor:
    """Handles audio inspection, conversion, and persistent temporary storage."""

    SUPPORTED_FORMATS = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".opus"]

    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """Extract duration and audio properties safely using av or soundfile."""
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0.0
        info = {
            "duration": 0.0,
            "sample_rate": 16000,
            "channels": 1,
            "format": Path(file_path).suffix.lower(),
            "size_mb": round(file_size / (1024 * 1024), 2),
        }

        # 1. Try PyAV (works for MP3, M4A, OGG/Opus, WAV, etc.)
        try:
            with av.open(file_path) as container:
                audio_streams = [s for s in container.streams if s.type == "audio"]
                if audio_streams:
                    stream = audio_streams[0]
                    if container.duration:
                        info["duration"] = round(float(container.duration / av.time_base), 2)
                    elif stream.duration and stream.time_base:
                        info["duration"] = round(float(stream.duration * stream.time_base), 2)
                    info["sample_rate"] = stream.rate or 16000
                    info["channels"] = stream.channels or 1
                    return info
        except Exception:
            pass

        # 2. Try SoundFile fallback
        try:
            with sf.SoundFile(file_path) as s:
                info["duration"] = round(len(s) / s.samplerate, 2)
                info["sample_rate"] = s.samplerate
                info["channels"] = s.channels
                return info
        except Exception:
            pass

        return info

    @staticmethod
    def save_upload_to_temp(uploaded_file, *args, **kwargs) -> str:
        """Save a streamlit uploaded file buffer deterministically to avoid redundant writes.
        Accepts any combination of positional or keyword arguments defensively.
        """
        file_signature = kwargs.get("file_signature", "")
        suffix = kwargs.get("suffix", "")

        if args:
            if len(args) == 1:
                arg0 = str(args[0])
                if arg0.startswith("."):
                    suffix = arg0
                else:
                    file_signature = arg0
            elif len(args) >= 2:
                file_signature = str(args[0])
                suffix = str(args[1])

        if not suffix:
            suffix = Path(getattr(uploaded_file, "name", "audio.wav")).suffix or ".wav"
        if not file_signature:
            file_signature = f"{getattr(uploaded_file, 'name', 'audio')}_{getattr(uploaded_file, 'size', 0)}"

        temp_dir = Path(tempfile.gettempdir()) / "echomind_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        hash_name = hashlib.md5(file_signature.encode('utf-8')).hexdigest()[:12]
        file_path = temp_dir / f"upload_{hash_name}{suffix}"

        if not file_path.exists():
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read())

        return str(file_path)
