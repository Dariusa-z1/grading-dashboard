import streamlit as st
import pandas as pd
from datetime import datetime


def render_export(df: pd.DataFrame, metrics: dict):
    st.header("Export Options")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 Export Processed Data")
        from streamlit.runtime.state.session_state_proxy import SessionStateProxy
        processed_df = df

        include_calculations = st.checkbox("Include calculated fields", value=True)
        include_flags_only = st.checkbox("Export flagged items only", value=False)

        export_df = processed_df[processed_df['auto_flag']] if include_flags_only else processed_df
        if not include_calculations:
            # Keep only original columns if available in session
            original_cols = set(st.session_state.get('data', pd.DataFrame()).columns)
            export_df = export_df[[c for c in export_df.columns if c in original_cols]]

        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"grading_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c2:
        st.subheader("📑 Generate Report")

        report_name = st.text_input("Report Title", value="Grading Analysis Report")
        include_plots = st.checkbox("Include visualizations", value=True)
        include_stats = st.checkbox("Include statistical analysis", value=True)
        include_recommendations = st.checkbox("Include recommendations", value=True)

        if st.button("Generate Report", type="primary", use_container_width=True):
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
                mime="text/markdown",
            )
            st.success("✅ Report generated!")