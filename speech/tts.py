import asyncio
import threading
import edge_tts

class TextToSpeech:
    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
    async def _generate(
        self,
        text: str,
    ) -> bytes:
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        )
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(
                    chunk["data"]
                )
        return b"".join(
            audio_chunks
        )
    def _run_async_in_thread(
        self,
        text: str,
    ) -> bytes:
        """
        Run async TTS in a separate thread.
        This avoids calling asyncio.run() inside
        an already-running FastAPI event loop.
        """
        result = {
            "audio": None,
            "error": None,
        }
        def runner():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(
                    loop
                )
                try:
                    result["audio"] = (
                        loop.run_until_complete(
                            self._generate(text)
                        )
                    )
                finally:
                    loop.close()
            except Exception as exc:
                result["error"] = exc
        thread = threading.Thread(
            target=runner,
            daemon=True,
        )
        thread.start()
        thread.join()
        if result["error"] is not None:
            raise result["error"]
        return result["audio"]
    def generate(
        self,
        text: str,
    ) -> bytes:
        if not text or not text.strip():
            raise ValueError(
                "TTS text cannot be empty."
            )
        return self._run_async_in_thread(
            text.strip()
        )