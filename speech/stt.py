import os
import tempfile
from typing import Optional
from faster_whisper import WhisperModel

class SpeechToText:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = "en",
    ) -> str:
        if not audio_bytes:
            raise ValueError(
                "Audio data is empty."
            )
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as file:
                file.write(audio_bytes)
                temp_path = file.name
            segments, _ = self.model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            transcript = " ".join(
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            ).strip()
            if not transcript:
                raise ValueError(
                    "Could not understand the audio."
                )
            return transcript
        finally:
            if temp_path and os.path.exists(
                temp_path
            ):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass