"""Transcription of audio files with Whisper."""

import whisper

_model = None


def _get_model():
    """Return the shared Whisper model and load it on the first call."""
    global _model

    if _model is None:
        _model = whisper.load_model("turbo")

    return _model


def transcribe(audio_path: str) -> str:
    """Transcribe an audio file to text.

    Args:
        audio_path: Path of the audio file. ffmpeg has to be installed to read it.

    Returns:
        The transcript.
    """
    result = _get_model().transcribe(audio_path)

    return result["text"]
