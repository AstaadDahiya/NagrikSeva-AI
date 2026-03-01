"""
NagrikSeva AI — Speech-to-Text Helper
=======================================
Lightweight STT utilities for processing Twilio SpeechResult transcriptions.
For production, replace Twilio STT with Deepgram Nova-2 with language="hi"
for significantly better Hindi accuracy.
"""

import re
import logging

from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Common noise patterns from Twilio STT
NOISE_PATTERNS = [
    r"^\[.*\]$",       # [inaudible], [noise], etc.
    r"^(hmm|um|uh|ah|oh|hm)+[.\s]*$",  # filler sounds only
    r"^[\s.,!?]+$",    # punctuation only
]


def clean_transcript(text: str) -> str:
    """
    Clean raw Twilio SpeechResult text.
    
    - Strips extra whitespace
    - Fixes common Twilio STT errors for Hindi words
    - Normalizes punctuation
    
    Args:
        text: Raw SpeechResult from Twilio
    
    Returns:
        Cleaned transcript string
    """
    if not text:
        return ""
    
    # Strip leading/trailing whitespace
    cleaned = text.strip()
    
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    
    # Common Twilio STT corrections for Hindi words
    corrections = {
        "namaste": "namaste",
        "namaskar": "namaskar",
        "shiqayat": "shikayat",
        "shikayaat": "shikayat",
        "bijlee": "bijli",
        "paani": "paani",
        "sadak": "sadak",
        "safaai": "safai",
        "swaasthya": "swasthya",
        "dhanyavaad": "dhanyawad",
        "dhanyawaad": "dhanyawad",
        "shukriya": "shukriya",
    }
    
    lower = cleaned.lower()
    for wrong, right in corrections.items():
        lower = lower.replace(wrong, right)
    
    # Keep original case if no corrections, else use corrected lowercase
    if lower != cleaned.lower():
        cleaned = lower
    
    return cleaned


def is_intelligible(text: str) -> bool:
    """
    Check if the transcribed text is intelligible enough to process.
    
    Returns False if:
    - Text is empty or whitespace-only
    - Text has fewer than 2 words
    - Text matches noise patterns (filler sounds, [inaudible], etc.)
    
    Args:
        text: Cleaned transcript text
    
    Returns:
        True if text appears intelligible, False otherwise
    """
    if not text or not text.strip():
        return False
    
    stripped = text.strip()
    
    # Check word count
    words = stripped.split()
    if len(words) < 2:
        # Allow single meaningful words (names, numbers, yes/no)
        single = stripped.lower()
        meaningful_singles = {
            "haan", "nahi", "yes", "no", "theek", "sahi", "galat",
            "roads", "water", "electricity", "sanitation", "health", "other",
            "sadak", "paani", "bijli", "safai",
        }
        if single not in meaningful_singles and not single.isdigit():
            return False
    
    # Check noise patterns
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, stripped, re.IGNORECASE):
            return False
    
    return True


def detect_language(text: str) -> str:
    """
    Detect language of the given text using langdetect.
    
    Returns:
        'hindi' if Hindi/Urdu detected, 'english' if English, 'hinglish' if mixed/uncertain.
    """
    try:
        lang = detect(text)
        if lang in ("hi", "ur"):
            return "hindi"
        elif lang == "en":
            return "english"
        else:
            return "hinglish"
    except LangDetectException:
        return "hinglish"
    except Exception:
        return "hinglish"
