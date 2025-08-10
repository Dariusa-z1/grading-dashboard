import streamlit as st
import pandas as pd
from datetime import datetime


def render_review_queue(df: pd.DataFrame):
    st.header("Review Queue")
    st.markdown("Items flagged for manual review based on low confidence or high error")

    with st.expander("⚙️ Flagging Criteria"):
        st.write(
            """
            Items are automatically flagged if they meet any of these criteria:
            - Confidence < 0.6
            - Error > 25% of max points
            - Absolute error > 30% of max points
            - Manual flag = True
            """
        )

    flagged_df = df[df['auto_flag']].sort_values('abs_error', ascending=False).copy()

    if len(flagged_df) > 0:
        st.write(f"**Found {len(flagged_df)} items requiring review**")

        flagged_df['priority'] = pd.cut(
            flagged_df['percent_error'], bins=[0, 15, 30, 100], labels=['🟡 Low', '🟠 Medium', '🔴 High']
        )

        display_cols = st.multiselect(
            "Select columns to display:", options=flagged_df.columns.tolist(),
            default=['student_id', 'question_id', 'ta_score', 'llm_score', 'abs_error', 'percent_error', 'confidence', 'priority']
        )

        st.dataframe(flagged_df[display_cols].round(2), use_container_width=True, height=400)

        csv = flagged_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Review Queue as CSV",
            data=csv,
            file_name=f"review_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.success("✅ No items flagged for review!")