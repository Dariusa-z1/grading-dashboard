from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
from src.config import CONFIDENCE_THRESHOLD, PERCENT_ERROR_THRESHOLD, ABS_ERROR_FACTOR

REQUIRED_COLS = ['student_id', 'question_id', 'ta_score', 'llm_score', 'max_points']

@st.cache_data(show_spinner=False)
def load_data(uploaded_file) -> pd.DataFrame | None:
    """Load and validate CSV data."""
    try:
        df = pd.read_csv(uploaded_file)
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            st.error(f"Missing required columns: {missing}")
            return None
        if 'confidence' not in df.columns:
            df['confidence'] = 1.0
        if 'flags' not in df.columns:
            df['flags'] = False
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

@st.cache_data(show_spinner=False)
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived columns and auto flags."""
    df = df.copy()
    df['error'] = df['llm_score'] - df['ta_score']
    df['abs_error'] = np.abs(df['error'])
    df['percent_error'] = (df['abs_error'] / df['max_points'] * 100).round(2)
    df['normalized_ta'] = df['ta_score'] / df['max_points']
    df['normalized_llm'] = df['llm_score'] / df['max_points']
    df['auto_flag'] = (
        (df['confidence'] < CONFIDENCE_THRESHOLD) |
        (df['percent_error'] > PERCENT_ERROR_THRESHOLD) |
        (df['abs_error'] > df['max_points'] * ABS_ERROR_FACTOR)
    )
    return df

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply user-selected filters to dataframe."""
    out = df.copy()
    if filters.get('questions'):
        out = out[out['question_id'].isin(filters['questions'])]
    if filters.get('students'):
        out = out[out['student_id'].isin(filters['students'])]
    lo, hi = filters.get('confidence_range', (0.0, 1.0))
    out = out[(out['confidence'] >= lo) & (out['confidence'] <= hi)]
    out = out[out['percent_error'] <= filters.get('error_threshold', 100)]
    return out