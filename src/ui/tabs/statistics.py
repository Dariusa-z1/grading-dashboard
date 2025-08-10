import streamlit as st
import pandas as pd
from src.ui.components import bland_altman


def render_statistics(df: pd.DataFrame, metrics: dict):
    st.header("Statistical Analysis")

    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("📊 Statistical Tests")
        strength = lambda r: '🟢 Strong' if r > 0.7 else '🟡 Moderate' if r > 0.4 else '🔴 Weak'
        stats_data = {
            'Metric': [
                'Pearson Correlation', 'Spearman Correlation', 'Mean Bias', 'Std Deviation', 'RMSE', 'MAPE'
            ],
            'Value': [
                f"{metrics['pearson_r']:.3f}" if metrics['pearson_r'] == metrics['pearson_r'] else 'N/A',
                f"{metrics['spearman_r']:.3f}" if metrics['spearman_r'] == metrics['spearman_r'] else 'N/A',
                f"{metrics['mean_bias']:.2f}", f"{metrics['std_error']:.2f}", f"{metrics['rmse']:.2f}", f"{metrics['mape']:.1f}%"
            ],
            'Interpretation': [
                strength(metrics['pearson_r']) if metrics['pearson_r'] == metrics['pearson_r'] else '—',
                strength(metrics['spearman_r']) if metrics['spearman_r'] == metrics['spearman_r'] else '—',
                '🟢 Low' if abs(metrics['mean_bias']) < 1 else '🟡 Moderate' if abs(metrics['mean_bias']) < 2 else '🔴 High',
                '🟢 Low' if metrics['std_error'] < 1.5 else '🟡 Moderate' if metrics['std_error'] < 3 else '🔴 High',
                '🟢 Good' if metrics['rmse'] < 2 else '🟡 Fair' if metrics['rmse'] < 4 else '🔴 Poor',
                '🟢 Good' if metrics['mape'] < 15 else '🟡 Fair' if metrics['mape'] < 30 else '🔴 Poor',
            ],
        }
        st.dataframe(pd.DataFrame(stats_data), hide_index=True, use_container_width=True)

    with c2:
        st.subheader("📈 Bland-Altman Plot")
        st.plotly_chart(bland_altman(df), use_container_width=True)

    st.subheader("📊 Question-Level Performance")
    question_stats = df.groupby('question_id').agg({
        'abs_error': ['mean', 'std', 'max'],
        'confidence': 'mean',
        'auto_flag': 'sum',
        'student_id': 'count',
    }).round(2)
    question_stats.columns = ['MAE', 'Std Dev', 'Max Error', 'Avg Confidence', 'Flagged', 'Count']
    st.dataframe(question_stats, use_container_width=True)