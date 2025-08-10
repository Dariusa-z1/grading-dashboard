# 📊 Grading Analysis Dashboard 

A Streamlit app to analyze and visualize automated grading results compared with TA scores.

## What it does
- 📂 **Load CSV** of grading results and validate required columns.
- 📏 **Compute metrics**: MAE, RMSE, MAPE, bias, correlations.
- 🚨 **Auto-flag risky items** (low confidence, large errors).
- 📈 **Interactive plots**: scatter, histograms, box plots, Bland–Altman.
- 🔍 **Filter** by question, confidence, and error threshold.
- 💾 **Export** processed/flagged data and generate a Markdown report.

## 📄 CSV schema
**Required columns**
- `student_id` (str)
- `question_id` (str)
- `ta_score` (float)
- `llm_score` (float)
- `max_points` (float/int)

**Optional columns (auto-added if missing)**
- `confidence` (float in [0,1], default 1.0)
- `flags` (bool, default False)

## 🚨 Auto-flag criteria
An item is flagged if **any** is true:
- `confidence < 0.6`
- `percent_error > 25` (|LLM−TA| / max_points * 100)
- `abs_error > 30%` of `max_points`

## 📊 Key metrics (per dataset / filtered view)
- **MAE**, **RMSE**, **MAPE**, **max error**
- **Pearson r** and **Spearman r**
- **Mean bias** and **std of error**
- Flag counts and percentages
- Question-level summary (MAE, confidence, flags, count)

## ⚙️ Install
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install streamlit pandas numpy plotly scipy
```

## ▶️ Run
```bash
streamlit run app.py
```
Then upload your CSV from the sidebar.

## 🗂 Tabs overview
- **📈 Overview** — KPIs, agreement scatter, error histogram, question box plot.
- **📊 Statistical Analysis** — Metrics, Bland–Altman, question table.
- **🔍 Deep Dive** — Per-question drill-down, student rankings.
- **⚠️ Review Queue** — Flagged items table + CSV download.
- **📑 Export** — Download processed data or summary report.

## 📤 Export outputs
- **review_queue_YYYYMMDD_HHMMSS.csv** (flagged items)
- **grading_analysis_YYYYMMDD_HHMMSS.csv** (full/filtered data)
- **report_YYYYMMDD_HHMMSS.md** (summary report)

## 💡 Notes
- 🧪 Generate a sample dataset from the welcome screen.
- 🚩 Large errors or low confidence suggest items to review.

---
**Version**: Dashboard v1.0 (Streamlit)
