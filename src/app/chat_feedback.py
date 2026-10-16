"""Shared waiting indicator and message-triggered scrolling for both chats."""

import hashlib
import json
from pathlib import Path

import streamlit.components.v1 as components


def render_text_stream(target, chunks):
    """Replace the waiting placeholder progressively without adding a cursor."""
    parts = []
    for chunk in chunks:
        parts.append(chunk)
        target.markdown("".join(parts))
    return "".join(parts)


TYPING_HTML = """
<style>
.chat-typing{display:flex;gap:6px;align-items:center;min-height:32px;padding:8px 2px}
.chat-typing span{width:7px;height:7px;border-radius:50%;background:#0f69b4;
 animation:chat-dot-wave 1.2s ease-in-out infinite}
.chat-typing span:nth-child(2){animation-delay:160ms}
.chat-typing span:nth-child(3){animation-delay:320ms}
@keyframes chat-dot-wave{0%,60%,100%{transform:translateY(0);opacity:.45}
 30%{transform:translateY(-6px);opacity:1}}
@media(prefers-reduced-motion:reduce){.chat-typing span{animation:none;opacity:.75}}
</style>
<div class="chat-typing" role="status" aria-label="El asistente está preparando tu respuesta">
<span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span>
</div>
"""
SCROLL_SCRIPT = (Path(__file__).parent / "assets/chat-scroll.html").read_text()


def scroll_chat(scope: str, event: str) -> None:
    """Scroll on a new sent/received event, without trapping later manual scrolling."""
    token = hashlib.sha256(event.encode()).hexdigest()
    components.html(
        SCROLL_SCRIPT.replace("__SCOPE__", json.dumps(scope)).replace(
            "__TOKEN__", json.dumps(token)
        ),
        height=0,
    )
