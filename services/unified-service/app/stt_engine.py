import io
import time
from typing import Tuple, List
# from faster_whisper import WhisperModel
from .config import STT_MODEL_SIZE, STT_DEVICE, STT_COMPUTE_TYPE
from .models import TranscriptionResult, TranscriptionSegment

# Mock model for testing - replace with actual WhisperModel when dependencies are installed
class MockWhisperModel:
    def transcribe(self, audio, language=None):
        class MockResult:
            def __init__(self):
                self.text = "test voice input"
                self.language = "en"
                self.segments = []
        return MockResult()

# Initialize model once at startup
# model = WhisperModel(
#     STT_MODEL_SIZE,
#     device=STT_DEVICE,          # "auto" picks best
#     compute_type=STT_COMPUTE_TYPE
# )
model = MockWhisperModel()  # Use mock for now

ALLOWED_MIME_TYPES = {
    "audio/wav", "audio/x-wav",
    "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/aac",
    "audio/x-m4a", "audio/m4a",
    "audio/ogg", "audio/webm",
    "audio/webm;codecs=opus",  # Browser WebM format
}

def transcribe_audio(file_bytes: bytes, detect_language: bool = True) -> TranscriptionResult:
    """
    Transcribe audio from bytes. Returns full text + optional segments.
    """
    # faster-whisper can accept a bytes-like object via file object
    audio_fp = io.BytesIO(file_bytes)
    t0 = time.time()
    segments, info = model.transcribe(audio_fp, beam_size=5, vad_filter=True)
    duration = time.time() - t0

    segs: List[TranscriptionSegment] = []
    full_text_parts = []
    for s in segments:
        segs.append(TranscriptionSegment(start=s.start, end=s.end, text=s.text.strip()))
        full_text_parts.append(s.text.strip())

    return TranscriptionResult(
        text=" ".join(full_text_parts).strip(),
        language=(info.language if detect_language else None),
        duration=duration,
        segments=segs
    )

def is_allowed_mime(mime: str) -> bool:
    if not mime:
        return False
    mime = mime.lower()
    if mime in ALLOWED_MIME_TYPES:
        return True
    # be lenient with parameters (e.g., audio/webm;codecs=opus)
    if mime.startswith("audio/webm"):
        return True
    # Also accept application/octet-stream for webm files (browser sometimes sends this)
    if mime == "application/octet-stream":
        return True
    return False

