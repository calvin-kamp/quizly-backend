import whisper

_model = None


def _get_model():
    global _model

    if _model is None:
        _model = whisper.load_model("turbo")

    return _model


def transcribe(audio_path: str) -> str:
    result = _get_model().transcribe(audio_path)

    return result["text"]
