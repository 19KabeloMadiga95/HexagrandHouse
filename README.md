# HexagrandHouse

Premium analytics platform for lottery intelligence, football predictions, model tracking and responsible-play analytics.

---

# Run Locally

## Create Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Install Requirements

```powershell
pip install -r requirements.txt
```

## Run Streamlit App

```powershell
streamlit run src/lottery/frontend/streamlit_app.py
```

---

# Daily Automation

## Lottery Cycle

```powershell
python -m src.lottery.automation.run_daily_lottery_cycle
```

## Football Cycle

```powershell
python -m src.football.automation.run_daily_football_cycle
```

---

# Key Frontend Structure

```text
src/lottery/frontend/pages/
src/lottery/frontend/components/
src/lottery/frontend/styles/
```

---

# Main Features

- Lottery predictions
- Football predictions
- Ensemble analytics
- Historical results
- Prediction backtesting
- Confidence tracking
- Model accuracy scoring
- Responsible play section

---

# Notes

This platform is intended for analytical entertainment and probabilistic evaluation only.
Predictions are not guarantees.