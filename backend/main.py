
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Defence Intelligence & Threat Analysis Platform",
    version="0.1.0"
)

# Allow the React frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Synthetic data for demonstration purposes only
reports = [
    {
        "id": 1,
        "title": "Severe Weather Disrupts Transport",
        "category": "Weather",
        "location": "Demo Region A",
        "source": "Synthetic demonstration data",
        "summary": "Heavy rainfall has disrupted transport in a fictional region.",
        "priority": "High"
    },
    {
        "id": 2,
        "title": "Emergency Services Issue Advisory",
        "category": "Public Safety",
        "location": "Demo Region A",
        "source": "Synthetic demonstration data",
        "summary": "Local services advise residents to follow official safety updates.",
        "priority": "Medium"
    },
    {
        "id": 3,
        "title": "Infrastructure Operating Normally",
        "category": "Infrastructure",
        "location": "Demo Region B",
        "source": "Synthetic demonstration data",
        "summary": "A fictional report describes normal infrastructure operations.",
        "priority": "Low"
    }
]


@app.get("/")
def home():
    return {
        "message": "Defence Intelligence Platform API",
        "status": "online"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/reports")
def get_reports(q: str = ""):
    if not q.strip():
        return reports

    query = q.lower()

    return [
        report for report in reports
        if query in (
            report["title"] + " " +
            report["category"] + " " +
            report["location"] + " " +
            report["summary"]
        ).lower()
    ]


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    for report in reports:
        if report["id"] == report_id:
            return report

    raise HTTPException(status_code=404, detail="Report not found")


@app.get("/analytics")
def get_analytics():
    return {
        "total_reports": len(reports),
        "high_priority": sum(
            report["priority"] == "High" for report in reports
        ),
        "medium_priority": sum(
            report["priority"] == "Medium" for report in reports
        ),
        "low_priority": sum(
            report["priority"] == "Low" for report in reports
        ),
        "data_type": "Synthetic demonstration data"
    }


@app.post("/analyze/{report_id}")
def analyze_report(report_id: int):
    report = next(
        (item for item in reports if item["id"] == report_id),
        None
    )

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "report_id": report_id,
        "title": report["title"],
        "priority": report["priority"],
        "method": "Demo rules-based analysis",
        "limitations": (
            "Demonstration only; this is not a validated AI prediction "
            "or real intelligence assessment."
        )
    }
