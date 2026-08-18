import os
import tempfile
from typing import Optional


class SpeechToText:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def _get_model(self):
        if self.model is None:
            # Lazy import — prevents faster-whisper from loading
            # at server startup and crashing Render free-tier RAM
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise RuntimeError(
                    "faster-whisper is not installed. "
                    "Add it to requirements.txt."
                ) from e
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self.model

    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = "en",
    ) -> str:
        if not audio_bytes:
            raise ValueError(
                "Audio data is empty."
            )
        model = self._get_model()
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as file:
                file.write(audio_bytes)
                temp_path = file.name
            segments, _ = model.transcribe(
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