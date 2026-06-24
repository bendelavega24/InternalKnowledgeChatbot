"""Suggestion chip rendering."""

import re

import streamlit as st

MAX_SUGGESTIONS = 3


def normalize_suggestions(suggestions):
    # Clean model suggestions into max 3 unique button labels.
    if not suggestions:
        return []

    if isinstance(suggestions, str):
        suggestions = [suggestions]

    cleaned = []
    seen = set()

    for suggestion in suggestions:
        for part in re.split(r"(?<=\?)\s+", str(suggestion or "").strip()):
            text = part.strip().lstrip("-•123456789. )").strip()
            key = text.lower()

            if not text or key in seen:
                continue

            seen.add(key)
            cleaned.append(text)

            if len(cleaned) >= MAX_SUGGESTIONS:
                return cleaned

    return cleaned[:MAX_SUGGESTIONS]


def hide_answer_controls_now():
    # Hide old actions/suggestions immediately after a suggestion click.
    st.session_state.is_generating = True
    st.session_state.hide_actions = True
    st.session_state.hide_suggestions = True
    st.session_state.pop("open_export_panel_key", None)


def set_suggested_query(suggestion):
    # Store clicked suggestion for chat_ui.get_user_query().
    # This runs before the rerun, so old suggestion chips disappear right away.
    st.session_state.suggested_query = suggestion
    hide_answer_controls_now()


def should_hide_suggestions():
    # Hide old suggestion chips while an answer is pending, streaming, or regenerating.
    return (
        st.session_state.get("hide_suggestions", False)
        or st.session_state.get("hide_actions", False)
        or st.session_state.get("is_generating", False)
        or st.session_state.get("regenerate_data") is not None
        or st.session_state.get("regenerate_index") is not None
        or st.session_state.get("suggested_query") is not None
    )


def display_suggestions(suggestions, message_index=None):
    # Render suggestion buttons and return clicked text.
    if should_hide_suggestions():
        return None

    suggestions = normalize_suggestions(suggestions)

    if not suggestions:
        return None

    clicked = None

    with st.container(key=f"suggestion_area_{message_index}"):
        for index, suggestion in enumerate(suggestions):
            if st.button(
                suggestion,
                key=f"suggestion_{message_index}_{index}",
                on_click=set_suggested_query,
                args=(suggestion,),
            ):
                clicked = suggestion

    return clicked
