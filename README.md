# Defence Intelligence & Threat Analysis Platform

## Overview

A web-based academic project for viewing, searching, and analysing sample intelligence reports. The platform displays report priority, risk scores, matched keywords, and explanations of the analysis.

The current analysis engine uses predefined keyword-based rules for demonstration purposes.

## Features

- Dashboard for viewing intelligence reports
- Search and filter reports
- Rule-based report analysis
- Risk scores from 0 to 100
- Priority classification: High, Medium, and Low
- Matched keywords and reasoning
- FastAPI backend with automated tests

## Technology Stack

**Frontend:** React, Vite, JavaScript, CSS

**Backend:** Python, FastAPI

**Testing:** Pytest

## Project Structure

```text
defence-intelligence-platform/
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
└── backend/
    ├── main.py
    ├── analysis.py
    ├── data_store.py
    ├── data/
    │   └── reports.json
    ├── tests/
    │   └── test_analysis.py
    └── requirements.txt
```

## Installation

### Prerequisites

Install Node.js with npm and Python 3.

### 1. Clone the repository

```bash
git clone https://github.com/Starlord0o7/defence-intelligence-platform.git
cd defence-intelligence-platform
```

### 2. Set up the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the backend

From the `backend` directory:

```bash
uvicorn main:app --reload --port 8000
```

Backend health check: http://127.0.0.1:8000/health

Interactive API documentation: http://127.0.0.1:8000/docs

### 4. Run the frontend

Open a second Terminal window:

```bash
cd ~/defence-intelligence-platform/frontend
npm install
npm run dev
```

Open the local URL displayed in the Terminal by Vite.

## API Example

To analyse report ID 1:

```bash
curl -X POST http://127.0.0.1:8000/analyze/1
```

The API response includes analysis information such as priority, risk score, matched keywords, and reasoning.

## Running Tests

```bash
cd ~/defence-intelligence-platform/backend
source .venv/bin/activate
python -m pytest -v
```

## Analysis Method

The current demonstration engine uses predefined keyword scores and thresholds:

- **High:** score of 60 or above
- **Medium:** score from 30 to 59
- **Low:** score below 30

Scores are limited to the range 0–100.

## Limitations

- The reports use synthetic demonstration data.
- The analysis engine is rule-based and is not a trained machine-learning model.
- The results have not been validated for real-world defence or intelligence decisions.
- The platform is intended for academic demonstration, not operational decision-making.

## Future Improvements

- Integrate and evaluate a trained machine-learning model
- Expand the report dataset
- Add further filtering and visualisation features
- Improve validation and testing

## Author

Developed as an academic project.
