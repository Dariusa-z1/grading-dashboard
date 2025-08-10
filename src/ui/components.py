import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def agreement_scatter(df: pd.DataFrame):
    fig = px.scatter(
        df,
        x='ta_score', y='llm_score', color='confidence', size='abs_error',
        hover_data=['student_id', 'question_id', 'percent_error'],
        color_continuous_scale='RdYlGn',
        labels={'ta_score': 'TA Score', 'llm_score': 'LLM Score', 'confidence': 'Confidence', 'abs_error': 'Absolute Error'},
        title='LLM vs TA Score Comparison',
    )
    vmin = min(df['ta_score'].min(), df['llm_score'].min())
    vmax = max(df['ta_score'].max(), df['llm_score'].max())
    fig.add_trace(
        go.Scatter(x=[vmin, vmax], y=[vmin, vmax], mode='lines', name='Perfect Agreement', line=dict(color='gray', dash='dash'))
    )
    fig.update_layout(height=500)
    return fig


def error_histogram(df: pd.DataFrame):
    fig_hist = px.histogram(
        df,
        x='error', nbins=30,
        title='Distribution of Score Differences (LLM - TA)',
        labels={'error': 'Score Difference', 'count': 'Frequency'},
    )
    fig_hist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Zero Bias")
    fig_hist.update_layout(height=400)
    return fig_hist


def error_box_by_question(df: pd.DataFrame):
    fig_box = px.box(
        df,
        x='question_id', y='error',
        title='Error Distribution by Question',
        labels={'error': 'Score Difference', 'question_id': 'Question'},
    )
    fig_box.add_hline(y=0, line_dash="dash", line_color="red")
    fig_box.update_layout(height=400)
    return fig_box


def bland_altman(df: pd.DataFrame):
    mean_scores = (df['ta_score'] + df['llm_score']) / 2
    diff_scores = df['error']

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mean_scores,
        y=diff_scores,
        mode='markers',
        name='Data Points',
        marker=dict(color=df['confidence'], colorscale='RdYlGn', showscale=True, colorbar=dict(title="Confidence")),
        text=df['student_id'] + ' - ' + df['question_id'],
        hovertemplate='%{text}<br>Mean: %{x:.2f}<br>Difference: %{y:.2f}',
    ))

    mean_diff = float(diff_scores.mean())
    std_diff = float(diff_scores.std())
    fig.add_hline(y=mean_diff, line_color="blue", line_width=2, annotation_text=f"Mean: {mean_diff:.2f}")
    fig.add_hline(y=mean_diff + 1.96*std_diff, line_color="red", line_dash="dash", annotation_text=f"Upper LoA: {mean_diff + 1.96*std_diff:.2f}")
    fig.add_hline(y=mean_diff - 1.96*std_diff, line_color="red", line_dash="dash", annotation_text=f"Lower LoA: {mean_diff - 1.96*std_diff:.2f}")

    fig.update_layout(title="Bland-Altman Analysis", xaxis_title="Mean of TA & LLM Scores", yaxis_title="Difference (LLM - TA)", height=400)
    return fig