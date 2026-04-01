"""
WYN360 Voice Input - Speech-to-text for hands-free coding.

Uses system microphone to capture speech and convert to text.
Supports multiple STT backends:
  1. Google Speech Recognition (free, no API key)
  2. OpenAI Whisper API (requires OPENAI_API_KEY)
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check for speech_recognition availability
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    sr = None


class VoiceBackend:
    GOOGLE = "google"
    WHISPER = "whisper"


@dataclass
class VoiceConfig:
    """Voice input configuration."""
    enabled: bool = False
    backend: str = VoiceBackend.GOOGLE
    language: str = "en-US"
    timeout: int = 10  # Max seconds to listen
    phrase_time_limit: int = 30  # Max seconds per phrase
    energy_threshold: int = 300  # Microphone sensitivity


class VoiceInputManager:
    """Manages speech-to-text input."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._recognizer = None
        self._microphone = None
        self.total_transcriptions = 0
        self.total_errors = 0

    @property
    def is_available(self) -> bool:
        """Check if voice input dependencies are installed."""
        return HAS_SPEECH_RECOGNITION

    def initialize(self) -> bool:
        """Initialize the speech recognizer and microphone."""
        if not HAS_SPEECH_RECOGNITION:
            logger.warning(
                "Voice input requires the 'SpeechRecognition' package. "
                "Install with: pip install SpeechRecognition pyaudio"
            )
            return False

        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.config.energy_threshold
            self._recognizer.dynamic_energy_threshold = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize voice input: {e}")
            return False

    def listen(self) -> Optional[str]:
        """
        Listen for speech and return transcribed text.

        Returns None if no speech detected or on error.
        """
        if not self._recognizer:
            if not self.initialize():
                return None

        try:
            with sr.Microphone() as source:
                logger.debug("Listening for speech...")
                # Adjust for ambient noise
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Listen for speech
                audio = self._recognizer.listen(
                    source,
                    timeout=self.config.timeout,
                    phrase_time_limit=self.config.phrase_time_limit,
                )

            # Transcribe
            text = self._transcribe(audio)
            if text:
                self.total_transcriptions += 1
                logger.debug(f"Transcribed: {text[:100]}...")
            return text

        except sr.WaitTimeoutError:
            logger.debug("No speech detected (timeout)")
            return None
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Voice input error: {e}")
            return None

    def _transcribe(self, audio) -> Optional[str]:
        """Transcribe audio using the configured backend."""
        try:
            if self.config.backend == VoiceBackend.WHISPER:
                return self._transcribe_whisper(audio)
            else:
                return self._transcribe_google(audio)
        except sr.UnknownValueError:
            logger.debug("Speech not understood")
            return None
        except sr.RequestError as e:
            logger.error(f"STT service error: {e}")
            self.total_errors += 1
            return None

    def _transcribe_google(self, audio) -> Optional[str]:
        """Transcribe using Google's free speech recognition."""
        return self._recognizer.recognize_google(
            audio, language=self.config.language
        )

    def _transcribe_whisper(self, audio) -> Optional[str]:
        """Transcribe using OpenAI Whisper API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("Whisper backend requires OPENAI_API_KEY")
            return None
        return self._recognizer.recognize_whisper_api(
            audio, api_key=api_key
        )

    def toggle(self) -> bool:
        """Toggle voice input on/off."""
        self.config.enabled = not self.config.enabled
        return self.config.enabled

    def get_status(self) -> dict:
        """Get voice input status."""
        return {
            "available": self.is_available,
            "enabled": self.config.enabled,
            "backend": self.config.backend,
            "language": self.config.language,
            "total_transcriptions": self.total_transcriptions,
            "total_errors": self.total_errors,
        }
