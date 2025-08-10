import streamlit as st
from src.services.data_service import apply_filters
from src.services.analytics_service import calculate_metrics
from src.ui.tabs.overview import render_overview
from src.ui.tabs.statistics import render_statistics
from src.ui.tabs.deep_dive import render_deep_dive
from src.ui.tabs.review_queue import render_review_queue
from src.ui.tabs.export_tab import render_export

def render_app(processed_df):
    df = apply_filters(processed_df, st.session_state.filters)
    metrics = calculate_metrics(df)

    st.title("📊 Grading Analysis Results")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", "📊 Statistical Analysis", "🔍 Deep Dive", "⚠️ Review Queue", "📑 Export"
    ])

    with tab1:
        render_overview(df, metrics)
    with tab2:
        render_statistics(df, metrics)
    with tab3:
        render_deep_dive(df)
    with tab4:
        render_review_queue(df)
    with tab5:
        render_export(df, metrics)
