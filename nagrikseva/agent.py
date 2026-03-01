"""
NagrikSeva AI — Gemini Conversation Manager
=============================================
Manages per-call AI chat sessions using Google Gemini 1.5 Flash.
Each phone call gets its own isolated chat session keyed by Twilio call_sid.

Uses the modern google-genai SDK (replaces deprecated google-generativeai).
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from langdetect import detect, LangDetectException

from prompts import get_system_prompt

logger = logging.getLogger(__name__)

# Gemini client (lazy init — deferred until first use so server starts even without API key)
_gemini_client = None

MODEL_NAME = "gemini-2.5-flash"


def _get_gemini_client() -> genai.Client:
    """Get or create the Gemini client lazily."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


# ---------- History compatibility ----------
# main.py's _extract_grievance_data accesses chat history via:
#   agent.sessions[call_sid]["chat"].history
#   msg.parts[0].text, msg.role
# We provide a lightweight shim so the same access pattern works.

@dataclass
class _Part:
    text: str

@dataclass
class _HistoryMessage:
    role: str           # "user" or "model"
    parts: list = field(default_factory=list)

class _ChatWrapper:
    """
    Wraps google.genai chat session and exposes a .history attribute
    compatible with the access pattern used in main.py.
    """
    def __init__(self, chat, system_instruction: str):
        self._chat = chat
        self._system_instruction = system_instruction
        self.history: list[_HistoryMessage] = []

    def send_message(self, user_message: str) -> str:
        """Send a message and return the response text."""
        response = self._chat.send_message(message=user_message)
        response_text = response.text.strip()

        # Record in our compatible history
        self.history.append(_HistoryMessage(role="user", parts=[_Part(text=user_message)]))
        self.history.append(_HistoryMessage(role="model", parts=[_Part(text=response_text)]))

        return response_text


# In-memory session store: {call_sid: {"chat": _ChatWrapper, "language": str, "data": dict}}
sessions: dict = {}


def detect_language(text: str) -> str:
    """
    Detect language of the given text.
    
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


def initialize_session(call_sid: str, language: str = "hinglish") -> None:
    """
    Create a new Gemini chat session for the given call_sid.
    
    Args:
        call_sid: Unique Twilio call identifier
        language: Initial language for the system prompt (hindi/english/hinglish)
    """
    try:
        system_instruction = get_system_prompt(language)

        chat = _get_gemini_client().chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

        wrapper = _ChatWrapper(chat, system_instruction)

        sessions[call_sid] = {
            "chat": wrapper,
            "language": language,
            "data": {},
        }
        logger.info(f"Session initialized for call_sid={call_sid}, language={language}")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini session for {call_sid}: {e}")
        raise


def get_response(call_sid: str, user_message: str) -> str:
    """
    Send a user message to the Gemini chat session and return the AI response.
    
    If no session exists for the call_sid, one is initialized first.
    
    Args:
        call_sid: Unique Twilio call identifier
        user_message: Transcribed citizen speech
    
    Returns:
        AI response text string
    """
    try:
        # Initialize session if not exists
        if call_sid not in sessions:
            detected_lang = detect_language(user_message)
            initialize_session(call_sid, detected_lang)
        
        session = sessions[call_sid]
        
        # Update detected language
        detected_lang = detect_language(user_message)
        session["language"] = detected_lang
        
        # Send message and get response via wrapper
        ai_text = session["chat"].send_message(user_message)
        
        logger.info(f"[{call_sid}] User: {user_message[:80]}...")
        logger.info(f"[{call_sid}] Agent: {ai_text[:80]}...")
        
        return ai_text
        
    except Exception as e:
        logger.error(f"Gemini response error for {call_sid}: {e}")
        return (
            "Maaf kijiye, technical issue aa rahi hai. "
            "Kripya kuch der baad dobara call karein. Dhanyawad."
        )


def end_session(call_sid: str) -> list:
    """
    End and remove the chat session for the given call_sid.
    
    Args:
        call_sid: Unique Twilio call identifier
    
    Returns:
        List of chat history messages (for saving to MongoDB)
    """
    history = []
    try:
        if call_sid in sessions:
            session = sessions[call_sid]
            wrapper = session["chat"]
            
            # Extract chat history from our wrapper
            for msg in wrapper.history:
                history.append({
                    "role": msg.role,
                    "content": msg.parts[0].text if msg.parts else "",
                })
            
            # Remove session from memory
            del sessions[call_sid]
            logger.info(f"Session ended for call_sid={call_sid}, history_length={len(history)}")
    except Exception as e:
        logger.error(f"Error ending session for {call_sid}: {e}")
    
    return history


def get_session_language(call_sid: str) -> str:
    """
    Get the current detected language for a call session.
    
    Returns:
        Language string or 'hinglish' if session not found.
    """
    if call_sid in sessions:
        return sessions[call_sid].get("language", "hinglish")
    return "hinglish"
