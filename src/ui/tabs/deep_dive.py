import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_deep_dive(df: pd.DataFrame):
    st.header("Deep Dive Analysis")

    selected_question = st.selectbox(
        "Select a question for detailed analysis:", options=sorted(df['question_id'].unique())
    )
    question_df = df[df['question_id'] == selected_question]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("MAE for this question", f"{question_df['abs_error'].mean():.2f}")
    with c2:
        corr = question_df[['ta_score', 'llm_score']].corr().iloc[0,1]
        st.metric("Correlation", f"{corr:.3f}")
    with c3:
        st.metric("Flagged items", f"{int(question_df['auto_flag'].sum())}")

    fig_detail = px.scatter(
        question_df, x='ta_score', y='llm_score', color='confidence',
        hover_data=['student_id', 'percent_error'],
        title=f'Detailed Analysis for {selected_question}',
        labels={'ta_score': 'TA Score', 'llm_score': 'LLM Score'}
    )
    vmin = question_df[['ta_score', 'llm_score']].min().min()
    vmax = question_df[['ta_score', 'llm_score']].max().max()
    fig_detail.add_trace(go.Scatter(x=[vmin, vmax], y=[vmin, vmax], mode='lines', name='Perfect Agreement', line=dict(color='gray', dash='dash')))
    st.plotly_chart(fig_detail, use_container_width=True)

    st.subheader("Student Performance Distribution")
    student_stats = df.groupby('student_id').agg({
        'abs_error': 'mean', 'percent_error': 'mean', 'auto_flag': 'sum'
    }).sort_values('abs_error', ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.write("**🔴 Highest Error Students (Need Review)**")
        st.dataframe(student_stats.head(10).round(2), use_container_width=True)
    with c2:
        st.write("**🟢 Best Agreement Students**")
        st.dataframe(student_stats.tail(10).round(2), use_container_width=True)