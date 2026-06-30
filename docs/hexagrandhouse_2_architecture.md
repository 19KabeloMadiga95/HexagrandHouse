# HexagrandHouse 2.0 Architecture

## 1. Platform Goal
HexagrandHouse is a lightweight analytics platform for lottery intelligence, football intelligence, prediction generation, model monitoring, and dashboard delivery.

## 2. New Architecture Principle
Move from script-centric development to engine-centric development.

Old:
- many standalone scripts
- many Excel outputs
- scattered rules
- unclear entry points

New:
- one pipeline per engine
- centralized configuration
- SQLite-first data layer
- Streamlit dashboard reads from query service
- legacy scripts archived safely

## 3. Target Folder Structure

src/
  app/
  automation/
  core/
  data/
  lottery/
  football/
  api/

## 4. Engine Responsibilities

### Lottery Engine
Responsible for:
- history ingestion
- game rules
- feature creation
- prediction generation
- ensemble selection
- optimisation
- backtesting
- reporting

### Football Engine
Responsible for:
- fixture ingestion
- historical match data
- feature creation
- prediction generation
- value signals
- backtesting
- reporting

### Data Layer
Responsible for:
- SQLite database build
- reusable query service
- database health
- future PostgreSQL migration

### App Layer
Responsible for:
- Streamlit pages
- reusable visual components
- CSS/theme/assets
- user-facing navigation

### Automation Layer
Responsible for:
- daily cycle
- weekly cycle
- scheduled GitHub Actions
- refresh marker

## 5. Migration Rules

- Do not delete legacy scripts immediately.
- Move unused/old scripts into `_archive/legacy_scripts`.
- Keep one public pipeline entry point per engine.
- Keep rules/config outside model files.
- Keep frontend pages free from raw Excel reads.
- All dashboard reads should go through query_service.

## 6. Target Modules

### 6.1 Core

| Module | Purpose |
|---|---|
| `src/core/paths.py` | Central project paths. No hardcoded paths inside engine scripts. |
| `src/core/rules/lottery_rules.py` | Lotto, PowerBall, Daily Lotto, UK49s game rules. |
| `src/core/logging.py` | Standard logging helpers. |
| `src/core/utils.py` | Shared utility functions. |

### 6.2 Data Layer

| Module | Purpose |
|---|---|
| `src/data/database.py` | SQLite connection and generic table reads. |
| `src/data/query_service.py` | Business-friendly queries for dashboard and reports. |
| `src/data/build_database.py` | Builds `hexagrandhouse.db` from engine outputs. |

### 6.3 Lottery Engine

| Module | Purpose |
|---|---|
| `src/lottery/pipeline.py` | Main lottery entry point. Runs ingestion, features, models, optimisation, exports. |
| `src/lottery/ingestion.py` | Updates lottery historical results. |
| `src/lottery/features.py` | Builds lottery feature tables. |
| `src/lottery/prediction_engine.py` | Generates predictions for all lottery games. |
| `src/lottery/optimiser.py` | Handles ticket optimisation/diversity logic. |
| `src/lottery/backtesting.py` | Validates model performance against past results. |
| `src/lottery/reporting.py` | Exports dashboard-ready prediction/report files. |

### 6.4 Football Engine

| Module | Purpose |
|---|---|
| `src/football/pipeline.py` | Main football entry point. Runs fixtures, features, predictions, value, exports. |
| `src/football/fixtures.py` | Ingests upcoming fixtures from online/manual sources. |
| `src/football/history.py` | Maintains historical football results. |
| `src/football/features.py` | Builds football model features. |
| `src/football/prediction_engine.py` | Generates fixture predictions. |
| `src/football/value_engine.py` | Generates value bet signals. |
| `src/football/backtesting.py` | Scores predictions against completed fixtures. |
| `src/football/reporting.py` | Exports dashboard-ready football reports. |

### 6.5 App Layer

| Module | Purpose |
|---|---|
| `src/app/streamlit_app.py` | Streamlit app entry point. |
| `src/app/pages/` | Dashboard pages only. No heavy modelling logic. |
| `src/app/components/` | Reusable cards, charts, controls. |
| `src/app/styles/` | CSS/theme. |
| `src/app/assets/` | Logos/images. |

### 6.6 Automation

| Module | Purpose |
|---|---|
| `src/automation/daily_cycle.py` | Single daily pipeline entry point. |
| `src/automation/weekly_cycle.py` | Weekly retraining/backtesting if needed. |
| `src/automation/refresh_marker.py` | Writes cloud refresh timestamps. |

## 7. Migration Map

### 7.1 High-Level Migration

| Current Area | New Area | Action |
|---|---|---|
| `src/lottery/frontend/` | `src/app/` | Move after imports are stabilized. |
| `src/database/` | `src/data/` | Rename later; currently stable. |
| `src/lottery/config/` | `src/core/rules/` | Move lottery rules into shared core. |
| `src/lottery/models/` | `src/lottery/prediction_engine.py` | Consolidate gradually. |
| `src/lottery/optimization/` | `src/lottery/optimiser.py` | Consolidate gradually. |
| `src/football/data_ingestion/` | `src/football/fixtures.py` and `src/football/history.py` | Split by responsibility. |
| `src/football/predictions/` | `src/football/prediction_engine.py` | Consolidate gradually. |
| `src/football/value/` | `src/football/value_engine.py` | Consolidate gradually. |
| `.github/workflows/daily-cycles.yml` | unchanged | Later point to `src.automation.daily_cycle`. |

### 7.2 Migration Order

1. Centralize paths.
2. Centralize lottery rules.
3. Create `src/automation/daily_cycle.py`.
4. Update GitHub Actions to call one daily cycle.
5. Consolidate database layer.
6. Consolidate lottery engine.
7. Consolidate football engine.
8. Move frontend to `src/app`.
9. Archive legacy scripts.

### 7.3 Safety Rules

- One migration per commit.
- Run local pipeline after each migration.
- Run Streamlit after each frontend change.
- Do not delete legacy scripts until replacement works.
- Archive first, delete later.