import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from src.config import APP_TITLE, PAGE_ICON, LAYOUT
from src.services.data_service import load_data, process_data
from src.services.analytics_service import calculate_metrics
from src.ui.layout import render_app
from src.utils.session import ensure_state

# Page configuration
st.set_page_config(page_title=APP_TITLE, page_icon=PAGE_ICON, layout=LAYOUT, initial_sidebar_state="expanded")

# Load CSS
with open("assets/style.css", "r", encoding="utf-8") as f:
    st.markdown(f"""
    <style>{f.read()}</style>
    """, unsafe_allow_html=True)

# Initialize session state keys
ensure_state(
    data=None,
    processed_data=None,
    metrics=None,
    filters={
        'questions': [],
        'students': [],
        'confidence_range': (0.0, 1.0),
        'error_threshold': 100,
    },
)

# Sidebar
with st.sidebar:
    st.title("📊 Grading Dashboard")
    st.markdown("---")

    st.header("📤 Data Upload")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload grading results CSV with columns: student_id, question_id, ta_score, llm_score, max_points",
    )

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.data = df
            st.session_state.processed_data = process_data(df)
            st.success(f"✅ Loaded {len(df)} records")

    # Filters live only when we have data
    if st.session_state.processed_data is not None:
        # Sidebar mini-metrics
        m = calculate_metrics(st.session_state.processed_data)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Students", m['total_students'])
        with c2:
            st.metric("Questions", m['total_questions'])

        # Filters
        from src.ui.tabs.overview import render_sidebar_filters
        render_sidebar_filters(st.session_state.processed_data)

# Main content
if st.session_state.processed_data is None:
    # Welcome screen
    st.title("🎓 Automated Grading Analysis Dashboard")
    st.markdown(
        """
        ### Welcome! This dashboard helps you analyze automated grading results.

        **To get started:**
        1. Upload a CSV file with your grading results using the sidebar
        2. The CSV should contain these columns:
           - `student_id`: Student identifier
           - `question_id`: Question identifier  
           - `ta_score`: Human grader score
           - `llm_score`: AI model score
           - `max_points`: Maximum possible points
           - `confidence` (optional): Model confidence score
           - `flags` (optional): Manual review flags

        **Features:**
        - 📊 Interactive visualizations
        - 📈 Statistical analysis
        - 🔍 Error pattern detection
        - ⚠️ Automatic flagging of problematic cases
        - 📑 Exportable reports
        """
    )

    
    if st.button("Load Built-in Sample", type="primary"):
        # Load a bundled synthetic dataset from ./data/test_grading_data.csv
        sample_path = Path(__file__).parent / "data" / "test_grading_data.csv"
        try:
            sample_df = pd.read_csv(sample_path)
        except FileNotFoundError:
            st.error(f"Couldn't find sample file at {sample_path}. Make sure it exists.")
        except Exception as e:
            st.error(f"Error reading sample file: {e}")
        else:
            st.session_state.data = sample_df
            st.session_state.processed_data = process_data(sample_df)
            st.success("✅ Sample data loaded!")
            st.rerun()

else:
    render_app(st.session_state.processed_data)

# Footer
st.markdown("---")
st.markdown("<div class='footer'>Grading Analysis Dashboard | Built with Streamlit</div>", unsafe_allow_html=True)