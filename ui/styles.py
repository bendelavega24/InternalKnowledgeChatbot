"""Load the Streamlit custom CSS."""

from pathlib import Path

import streamlit as st

CSS_PATHS = [
    Path("ui/styles/main.css"),
    Path("main.css"),
]


def find_css_path():
    # First existing CSS path wins.
    for css_path in CSS_PATHS:
        if css_path.exists():
            return css_path

    return None


def load_css():
    # Load CSS once per rerun.
    css_path = find_css_path()

    if not css_path:
        st.warning("Custom CSS file was not found.")
        return

    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
