"""Browser dictation with explicit transcript review and duplicate-submit protection."""

import hashlib
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_component = components.declare_component(
    "chat_voice_input", path=str(Path(__file__).parent / "assets/voice_input")
)


def spoken_text(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", text)
    text = re.sub(r"https?://(?:www\.)?chileatiende\.gob\.cl\S*", "ChileAtiende", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*#_`|]", "", text)
    return re.sub(r"\s+", " ", text).strip()[:8000]


def voice_input(
    key: str, *, reply: str = "", message_id: str = "", compact: bool = False
) -> str | None:
    read_aloud = False if compact else st.toggle(
        "Leer respuestas en voz alta", key=f"{key}_read_aloud", value=False
    )
    text = spoken_text(reply)
    speech_id = message_id + hashlib.sha256(text.encode()).hexdigest()
    value = _component(
        key=key, default=None, reply_text=text, speech_id=speech_id, read_aloud=read_aloud,
        compact=compact
    )
    if not isinstance(value, dict):
        return None
    event_id, text = value.get("id"), value.get("text")
    if not isinstance(event_id, str) or not isinstance(text, str):
        return None
    consumed_key = f"{key}_consumed"
    if st.session_state.get(consumed_key) == event_id:
        return None
    st.session_state[consumed_key] = event_id
    return text.strip()[:2000] or None
