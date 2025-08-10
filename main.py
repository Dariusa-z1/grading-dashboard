import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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

    if st.button("Generate Sample Data", type="primary"):
        np.random.seed(42)
        n_students, n_questions = 30, 6
        data = []
        for sid in range(1, n_students + 1):
            for qid in range(1, n_questions + 1):
                max_pts = 10 if qid <= 3 else 15
                ta_score = np.random.uniform(max_pts * 0.4, max_pts * 0.95)
                llm_score = ta_score + np.random.normal(0, max_pts * 0.1)
                llm_score = np.clip(llm_score, 0, max_pts)
                confidence = float(np.clip(1 - abs(llm_score - ta_score) / max_pts, 0.3, 1))
                data.append({
                    'student_id': f'S{sid:03d}',
                    'question_id': f'Q{qid}',
                    'ta_score': round(float(ta_score), 2),
                    'llm_score': round(float(llm_score), 2),
                    'max_points': max_pts,
                    'confidence': round(confidence, 3),
                    'flags': confidence < 0.5,
                })
        sample_df = pd.DataFrame(data)
        st.session_state.data = sample_df
        st.session_state.processed_data = process_data(sample_df)
        st.success("✅ Sample data generated!")
        st.rerun()
else:
    render_app(st.session_state.processed_data)

# Footer
st.markdown("---")
st.markdown("<div class='footer'>Grading Analysis Dashboard | Built with Streamlit</div>", unsafe_allow_html=True)