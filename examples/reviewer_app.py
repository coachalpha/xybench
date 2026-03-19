"""Streamlit reviewer app for xybench.

Run with:
    streamlit run examples/reviewer_app.py
"""

import streamlit as st

st.set_page_config(page_title="xybench Review", layout="wide")
st.title("xybench Review Dashboard")

session_filter = st.sidebar.text_input("Filter by session ID (optional):")
output_filter = st.sidebar.text_input("View specific output ID (optional):")

from xybench.streamlit import ReviewComponent

ReviewComponent(
    session_id=session_filter or None,
    output_id=output_filter or None,
)
