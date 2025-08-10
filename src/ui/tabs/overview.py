import streamlit as st
import pandas as pd
from src.ui.components import agreement_scatter, error_histogram, error_box_by_question


def render_sidebar_filters(processed_df: pd.DataFrame):
    st.markdown("---")
    st.header("🔍 Filters")

    all_questions = sorted(processed_df['question_id'].unique())
    selected_questions = st.multiselect(
        "Select Questions", options=all_questions, default=[], key='question_filter'
    )
    st.session_state.filters['questions'] = selected_questions

    confidence_range = st.slider(
        "Confidence Range", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.05, key='confidence_filter'
    )
    st.session_state.filters['confidence_range'] = confidence_range

    error_threshold = st.slider(
        "Max Error % to Display", min_value=0, max_value=100, value=100, step=5, key='error_filter'
    )
    st.session_state.filters['error_threshold'] = error_threshold

    if st.button("🔄 Reset Filters", type="secondary", use_container_width=True):
        st.session_state.filters = {
            'questions': [], 'students': [], 'confidence_range': (0.0, 1.0), 'error_threshold': 100
        }
        st.rerun()


def render_overview(df: pd.DataFrame, metrics: dict):
    st.header("Performance Overview")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Mean Absolute Error", f"{metrics['mae']:.2f}", help="Average absolute difference between TA and LLM scores")
    with c2:
        r = metrics['pearson_r']
        st.metric("Correlation (r)", f"{r:.3f}" if r == r else "N/A", help="Pearson correlation coefficient between TA and LLM scores")
    with c3:
        st.metric("Flagged Items", f"{metrics['flagged_count']}", delta=f"{metrics['flagged_percent']:.1f}%", delta_color="inverse", help="Number of items requiring review")
    with c4:
        st.metric("Avg Confidence", f"{df['confidence'].mean():.2f}", help="Average model confidence across all graded items")

    st.subheader("Score Agreement Analysis")
    st.plotly_chart(agreement_scatter(df), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(error_histogram(df), use_container_width=True)
    with c2:
        st.plotly_chart(error_box_by_question(df), use_container_width=True)