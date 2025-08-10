"""
Grading Analysis Dashboard
A Streamlit application for analyzing and visualizing automated grading results
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Grading Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'filters' not in st.session_state:
    st.session_state.filters = {
        'questions': [],
        'students': [],
        'confidence_range': (0.0, 1.0),
        'error_threshold': 100
    }

# Utility functions
@st.cache_data
def load_data(uploaded_file):
    """Load and validate CSV data"""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Validate required columns
        required_cols = ['student_id', 'question_id', 'ta_score', 'llm_score', 'max_points']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            return None
            
        # Add optional columns if missing
        if 'confidence' not in df.columns:
            df['confidence'] = 1.0
        if 'flags' not in df.columns:
            df['flags'] = False
            
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

@st.cache_data
def process_data(df):
    """Process and enhance the dataframe with calculated fields"""
    df = df.copy()
    
    # Calculate additional metrics
    df['error'] = df['llm_score'] - df['ta_score']
    df['abs_error'] = np.abs(df['error'])
    df['percent_error'] = (df['abs_error'] / df['max_points'] * 100).round(2)
    df['normalized_ta'] = df['ta_score'] / df['max_points']
    df['normalized_llm'] = df['llm_score'] / df['max_points']
    
    # Auto-flagging logic
    df['auto_flag'] = (
        (df['confidence'] < 0.6) |
        (df['percent_error'] > 25) |
        (df['abs_error'] > df['max_points'] * 0.3)
    )
    
    return df

def calculate_metrics(df):
    """Calculate comprehensive metrics"""
    metrics = {}
    
    # Basic statistics
    metrics['total_items'] = len(df)
    metrics['total_students'] = df['student_id'].nunique()
    metrics['total_questions'] = df['question_id'].nunique()
    
    # Error metrics
    metrics['mae'] = np.mean(df['abs_error'])
    metrics['rmse'] = np.sqrt(np.mean(df['error'] ** 2))
    metrics['mape'] = np.mean(np.abs(df['error'] / (df['ta_score'] + 1e-10))) * 100
    metrics['max_error'] = df['abs_error'].max()
    
    # Correlation metrics
    from scipy import stats
    metrics['pearson_r'], metrics['pearson_p'] = stats.pearsonr(df['ta_score'], df['llm_score'])
    metrics['spearman_r'], metrics['spearman_p'] = stats.spearmanr(df['ta_score'], df['llm_score'])
    
    # Agreement metrics
    metrics['mean_bias'] = np.mean(df['error'])
    metrics['std_error'] = np.std(df['error'])
    
    # Flagging metrics
    metrics['flagged_count'] = df['auto_flag'].sum()
    metrics['flagged_percent'] = metrics['flagged_count'] / metrics['total_items'] * 100
    metrics['low_confidence_count'] = (df['confidence'] < 0.6).sum()
    metrics['high_error_count'] = (df['percent_error'] > 25).sum()
    
    # Per-question summary
    metrics['question_performance'] = df.groupby('question_id').agg({
        'abs_error': 'mean',
        'confidence': 'mean',
        'auto_flag': 'sum'
    }).to_dict()
    
    return metrics

def apply_filters(df, filters):
    """Apply user-selected filters to dataframe"""
    filtered_df = df.copy()
    
    if filters['questions']:
        filtered_df = filtered_df[filtered_df['question_id'].isin(filters['questions'])]
    
    if filters['students']:
        filtered_df = filtered_df[filtered_df['student_id'].isin(filters['students'])]
    
    filtered_df = filtered_df[
        (filtered_df['confidence'] >= filters['confidence_range'][0]) &
        (filtered_df['confidence'] <= filters['confidence_range'][1])
    ]
    
    filtered_df = filtered_df[filtered_df['percent_error'] <= filters['error_threshold']]
    
    return filtered_df

# Sidebar
with st.sidebar:
    st.title("📊 Grading Dashboard")
    st.markdown("---")
    
    # File upload
    st.header("📤 Data Upload")
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload grading results CSV with columns: student_id, question_id, ta_score, llm_score, max_points"
    )
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.data = df
            st.session_state.processed_data = process_data(df)
            st.session_state.metrics = calculate_metrics(st.session_state.processed_data)
            st.success(f"✅ Loaded {len(df)} records")
            
            # Display basic info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Students", st.session_state.metrics['total_students'])
            with col2:
                st.metric("Questions", st.session_state.metrics['total_questions'])
    
    # Filters section
    if st.session_state.processed_data is not None:
        st.markdown("---")
        st.header("🔍 Filters")
        
        df = st.session_state.processed_data
        
        # Question filter
        all_questions = sorted(df['question_id'].unique())
        selected_questions = st.multiselect(
            "Select Questions",
            options=all_questions,
            default=[],
            key='question_filter'
        )
        st.session_state.filters['questions'] = selected_questions
        
        # Confidence filter
        confidence_range = st.slider(
            "Confidence Range",
            min_value=0.0,
            max_value=1.0,
            value=(0.0, 1.0),
            step=0.05,
            key='confidence_filter'
        )
        st.session_state.filters['confidence_range'] = confidence_range
        
        # Error threshold
        error_threshold = st.slider(
            "Max Error % to Display",
            min_value=0,
            max_value=100,
            value=100,
            step=5,
            key='error_filter'
        )
        st.session_state.filters['error_threshold'] = error_threshold
        
        # Apply filters button
        if st.button("🔄 Reset Filters", type="secondary", use_container_width=True):
            st.session_state.filters = {
                'questions': [],
                'students': [],
                'confidence_range': (0.0, 1.0),
                'error_threshold': 100
            }
            st.rerun()

# Main content area
if st.session_state.processed_data is None:
    # Welcome screen
    st.title("🎓 Automated Grading Analysis Dashboard")
    st.markdown("""
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
    """)
    
    # Sample data generation option
    if st.button("Generate Sample Data", type="primary"):
        np.random.seed(42)
        n_students = 30
        n_questions = 6
        
        data = []
        for sid in range(1, n_students + 1):
            for qid in range(1, n_questions + 1):
                max_pts = 10 if qid <= 3 else 15
                ta_score = np.random.uniform(max_pts * 0.4, max_pts * 0.95)
                llm_score = ta_score + np.random.normal(0, max_pts * 0.1)
                llm_score = np.clip(llm_score, 0, max_pts)
                confidence = np.clip(1 - abs(llm_score - ta_score) / max_pts, 0.3, 1)
                
                data.append({
                    'student_id': f'S{sid:03d}',
                    'question_id': f'Q{qid}',
                    'ta_score': round(ta_score, 2),
                    'llm_score': round(llm_score, 2),
                    'max_points': max_pts,
                    'confidence': round(confidence, 3),
                    'flags': confidence < 0.5
                })
        
        sample_df = pd.DataFrame(data)
        st.session_state.data = sample_df
        st.session_state.processed_data = process_data(sample_df)
        st.session_state.metrics = calculate_metrics(st.session_state.processed_data)
        st.success("✅ Sample data generated!")
        st.rerun()

else:
    # Main dashboard with data
    df = apply_filters(st.session_state.processed_data, st.session_state.filters)
    metrics = calculate_metrics(df)
    
    # Header
    st.title("📊 Grading Analysis Results")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "📊 Statistical Analysis", 
        "🔍 Deep Dive",
        "⚠️ Review Queue",
        "📑 Export"
    ])
    
    with tab1:
        # Overview Tab
        st.header("Performance Overview")
        
        # Key metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Mean Absolute Error",
                f"{metrics['mae']:.2f}",
                delta=f"{metrics['mae'] - st.session_state.metrics['mae']:.2f}" if metrics != st.session_state.metrics else None,
                help="Average absolute difference between TA and LLM scores"
            )
        
        with col2:
            st.metric(
                "Correlation (r)",
                f"{metrics['pearson_r']:.3f}",
                delta=None,
                help="Pearson correlation coefficient between TA and LLM scores"
            )
        
        with col3:
            st.metric(
                "Flagged Items",
                f"{metrics['flagged_count']}",
                delta=f"{metrics['flagged_percent']:.1f}%",
                delta_color="inverse",
                help="Number of items requiring review"
            )
        
        with col4:
            st.metric(
                "Avg Confidence",
                f"{df['confidence'].mean():.2f}",
                help="Average model confidence across all graded items"
            )
        
        # Main scatter plot
        st.subheader("Score Agreement Analysis")
        
        fig = px.scatter(
            df,
            x='ta_score',
            y='llm_score',
            color='confidence',
            size='abs_error',
            hover_data=['student_id', 'question_id', 'percent_error'],
            color_continuous_scale='RdYlGn',
            labels={
                'ta_score': 'TA Score',
                'llm_score': 'LLM Score',
                'confidence': 'Confidence',
                'abs_error': 'Absolute Error'
            },
            title='LLM vs TA Score Comparison'
        )
        
        # Add perfect agreement line
        min_val = min(df['ta_score'].min(), df['llm_score'].min())
        max_val = max(df['ta_score'].max(), df['llm_score'].max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Perfect Agreement',
                line=dict(color='gray', dash='dash')
            )
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Distribution plots
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist = px.histogram(
                df,
                x='error',
                nbins=30,
                title='Distribution of Score Differences (LLM - TA)',
                labels={'error': 'Score Difference', 'count': 'Frequency'}
            )
            fig_hist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Zero Bias")
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            fig_box = px.box(
                df,
                x='question_id',
                y='error',
                title='Error Distribution by Question',
                labels={'error': 'Score Difference', 'question_id': 'Question'}
            )
            fig_box.add_hline(y=0, line_dash="dash", line_color="red")
            fig_box.update_layout(height=400)
            st.plotly_chart(fig_box, use_container_width=True)
    
    with tab2:
        # Statistical Analysis Tab
        st.header("Statistical Analysis")
        
        # Correlation matrix
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📊 Statistical Tests")
            
            # Create a nice statistical summary
            stats_data = {
                'Metric': [
                    'Pearson Correlation',
                    'Spearman Correlation',
                    'Mean Bias',
                    'Std Deviation',
                    'RMSE',
                    'MAPE'
                ],
                'Value': [
                    f"{metrics['pearson_r']:.3f}",
                    f"{metrics['spearman_r']:.3f}",
                    f"{metrics['mean_bias']:.2f}",
                    f"{metrics['std_error']:.2f}",
                    f"{metrics['rmse']:.2f}",
                    f"{metrics['mape']:.1f}%"
                ],
                'Interpretation': [
                    '🟢 Strong' if metrics['pearson_r'] > 0.7 else '🟡 Moderate' if metrics['pearson_r'] > 0.4 else '🔴 Weak',
                    '🟢 Strong' if metrics['spearman_r'] > 0.7 else '🟡 Moderate' if metrics['spearman_r'] > 0.4 else '🔴 Weak',
                    '🟢 Low' if abs(metrics['mean_bias']) < 1 else '🟡 Moderate' if abs(metrics['mean_bias']) < 2 else '🔴 High',
                    '🟢 Low' if metrics['std_error'] < 1.5 else '🟡 Moderate' if metrics['std_error'] < 3 else '🔴 High',
                    '🟢 Good' if metrics['rmse'] < 2 else '🟡 Fair' if metrics['rmse'] < 4 else '🔴 Poor',
                    '🟢 Good' if metrics['mape'] < 15 else '🟡 Fair' if metrics['mape'] < 30 else '🔴 Poor'
                ]
            }
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
        
        with col2:
            # Bland-Altman plot
            st.subheader("📈 Bland-Altman Plot")
            
            mean_scores = (df['ta_score'] + df['llm_score']) / 2
            diff_scores = df['error']
            
            fig_ba = go.Figure()
            
            fig_ba.add_trace(go.Scatter(
                x=mean_scores,
                y=diff_scores,
                mode='markers',
                name='Data Points',
                marker=dict(
                    color=df['confidence'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Confidence")
                ),
                text=df['student_id'] + ' - ' + df['question_id'],
                hovertemplate='%{text}<br>Mean: %{x:.2f}<br>Difference: %{y:.2f}'
            ))
            
            # Add mean line and limits of agreement
            mean_diff = np.mean(diff_scores)
            std_diff = np.std(diff_scores)
            
            fig_ba.add_hline(y=mean_diff, line_color="blue", line_width=2, 
                           annotation_text=f"Mean: {mean_diff:.2f}")
            fig_ba.add_hline(y=mean_diff + 1.96*std_diff, line_color="red", line_dash="dash",
                           annotation_text=f"Upper LoA: {mean_diff + 1.96*std_diff:.2f}")
            fig_ba.add_hline(y=mean_diff - 1.96*std_diff, line_color="red", line_dash="dash",
                           annotation_text=f"Lower LoA: {mean_diff - 1.96*std_diff:.2f}")
            
            fig_ba.update_layout(
                title="Bland-Altman Analysis",
                xaxis_title="Mean of TA & LLM Scores",
                yaxis_title="Difference (LLM - TA)",
                height=400
            )
            
            st.plotly_chart(fig_ba, use_container_width=True)
        
        # Per-question detailed analysis
        st.subheader("📊 Question-Level Performance")
        
        question_stats = df.groupby('question_id').agg({
            'abs_error': ['mean', 'std', 'max'],
            'confidence': 'mean',
            'auto_flag': 'sum',
            'student_id': 'count'
        }).round(2)
        
        question_stats.columns = ['MAE', 'Std Dev', 'Max Error', 'Avg Confidence', 'Flagged', 'Count']
        st.dataframe(question_stats, use_container_width=True)
    
    with tab3:
        # Deep Dive Tab
        st.header("Deep Dive Analysis")
        
        # Question selector for detailed view
        selected_question = st.selectbox(
            "Select a question for detailed analysis:",
            options=sorted(df['question_id'].unique())
        )
        
        question_df = df[df['question_id'] == selected_question]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("MAE for this question", f"{question_df['abs_error'].mean():.2f}")
        with col2:
            st.metric("Correlation", f"{question_df[['ta_score', 'llm_score']].corr().iloc[0,1]:.3f}")
        with col3:
            st.metric("Flagged items", f"{question_df['auto_flag'].sum()}")
        
        # Detailed scatter for selected question
        fig_detail = px.scatter(
            question_df,
            x='ta_score',
            y='llm_score',
            color='confidence',
            hover_data=['student_id', 'percent_error'],
            title=f'Detailed Analysis for {selected_question}',
            labels={'ta_score': 'TA Score', 'llm_score': 'LLM Score'}
        )
        
        # Add perfect agreement line
        min_val = question_df[['ta_score', 'llm_score']].min().min()
        max_val = question_df[['ta_score', 'llm_score']].max().max()
        fig_detail.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Perfect Agreement',
                line=dict(color='gray', dash='dash')
            )
        )
        
        st.plotly_chart(fig_detail, use_container_width=True)
        
        # Student performance analysis
        st.subheader("Student Performance Distribution")
        
        student_stats = df.groupby('student_id').agg({
            'abs_error': 'mean',
            'percent_error': 'mean',
            'auto_flag': 'sum'
        }).sort_values('abs_error', ascending=False)
        
        # Show top/bottom performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔴 Highest Error Students (Need Review)**")
            st.dataframe(
                student_stats.head(10).round(2),
                use_container_width=True
            )
        
        with col2:
            st.write("**🟢 Best Agreement Students**")
            st.dataframe(
                student_stats.tail(10).round(2),
                use_container_width=True
            )
    
    with tab4:
        # Review Queue Tab
        st.header("Review Queue")
        st.markdown("Items flagged for manual review based on low confidence or high error")
        
        # Flagging criteria
        with st.expander("⚙️ Flagging Criteria"):
            st.write("""
            Items are automatically flagged if they meet any of these criteria:
            - Confidence < 0.6
            - Error > 25% of max points
            - Absolute error > 30% of max points
            - Manual flag = True
            """)
        
        # Get flagged items
        flagged_df = df[df['auto_flag']].sort_values('abs_error', ascending=False)
        
        if len(flagged_df) > 0:
            st.write(f"**Found {len(flagged_df)} items requiring review**")
            
            # Priority levels
            flagged_df['priority'] = pd.cut(
                flagged_df['percent_error'],
                bins=[0, 15, 30, 100],
                labels=['🟡 Low', '🟠 Medium', '🔴 High']
            )
            
            # Display options
            display_cols = st.multiselect(
                "Select columns to display:",
                options=flagged_df.columns.tolist(),
                default=['student_id', 'question_id', 'ta_score', 'llm_score', 
                        'abs_error', 'percent_error', 'confidence', 'priority']
            )
            
            # Show flagged items
            st.dataframe(
                flagged_df[display_cols].round(2),
                use_container_width=True,
                height=400
            )
            
            # Download flagged items
            csv = flagged_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Review Queue as CSV",
                data=csv,
                file_name=f"review_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.success("✅ No items flagged for review!")
    
    with tab5:
        # Export Tab
        st.header("Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Processed Data")
            
            # Export options
            include_calculations = st.checkbox("Include calculated fields", value=True)
            include_flags_only = st.checkbox("Export flagged items only", value=False)
            
            export_df = flagged_df if include_flags_only else df
            
            if not include_calculations:
                export_df = export_df[st.session_state.data.columns]
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"grading_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.subheader("📑 Generate Report")
            
            report_name = st.text_input("Report Title", value="Grading Analysis Report")
            include_plots = st.checkbox("Include visualizations", value=True)
            include_stats = st.checkbox("Include statistical analysis", value=True)
            include_recommendations = st.checkbox("Include recommendations", value=True)
            
            if st.button("Generate Report", type="primary", use_container_width=True):
                # This would generate a comprehensive report
                # For now, we'll create a summary
                report = f"""
# {report_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- Total Items Analyzed: {metrics['total_items']}
- Mean Absolute Error: {metrics['mae']:.2f}
- Correlation: {metrics['pearson_r']:.3f}
- Items Flagged for Review: {metrics['flagged_count']} ({metrics['flagged_percent']:.1f}%)

## Key Findings
- Average model confidence: {df['confidence'].mean():.2f}
- Bias: LLM scores are on average {abs(metrics['mean_bias']):.2f} points {'higher' if metrics['mean_bias'] > 0 else 'lower'} than TA scores
- Agreement level: {'Excellent' if metrics['pearson_r'] > 0.8 else 'Good' if metrics['pearson_r'] > 0.6 else 'Moderate' if metrics['pearson_r'] > 0.4 else 'Poor'}

## Recommendations
{"- Model shows good agreement with TAs. Consider expanding automated grading." if metrics['pearson_r'] > 0.7 else "- Model needs improvement before wider deployment."}
{"- Review flagged items to identify patterns for prompt improvement." if metrics['flagged_count'] > 0 else ""}
{"- Focus on questions with highest error rates for prompt refinement." if metrics['mae'] > 2 else ""}
                """
                
                st.download_button(
                    label="📥 Download Report",
                    data=report,
                    file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
                
                st.success("✅ Report generated!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Grading Analysis Dashboard v1.0 | Built with Streamlit
</div>
""", unsafe_allow_html=True)