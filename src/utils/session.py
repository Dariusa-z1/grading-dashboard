import streamlit as st

def ensure_state(**defaults):
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v