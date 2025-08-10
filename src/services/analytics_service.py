from __future__ import annotations
import numpy as np
from scipy import stats
import pandas as pd

def calculate_metrics(df: pd.DataFrame) -> dict:
    """Calculate comprehensive metrics for the filtered dataframe."""
    m: dict = {}
    m['total_items'] = int(len(df))
    m['total_students'] = int(df['student_id'].nunique())
    m['total_questions'] = int(df['question_id'].nunique())

    # Error metrics
    m['mae'] = float(np.mean(df['abs_error']))
    m['rmse'] = float(np.sqrt(np.mean(df['error'] ** 2)))
    m['mape'] = float(np.mean(np.abs(df['error'] / (df['ta_score'] + 1e-10))) * 100)
    m['max_error'] = float(df['abs_error'].max())

    # Correlations
    if len(df) >= 2 and df['ta_score'].nunique() > 1 and df['llm_score'].nunique() > 1:
        m['pearson_r'], m['pearson_p'] = stats.pearsonr(df['ta_score'], df['llm_score'])
        m['spearman_r'], m['spearman_p'] = stats.spearmanr(df['ta_score'], df['llm_score'])
    else:
        m['pearson_r'] = m['spearman_r'] = float('nan')
        m['pearson_p'] = m['spearman_p'] = float('nan')

    # Agreement
    m['mean_bias'] = float(np.mean(df['error']))
    m['std_error'] = float(np.std(df['error']))

    # Flags
    m['flagged_count'] = int(df['auto_flag'].sum())
    m['flagged_percent'] = float(m['flagged_count'] / max(m['total_items'], 1) * 100)

    return m