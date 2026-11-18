import uuid

from pathlib import Path
from fastapi import UploadFile, File
from document_processor import extract_text, split_into_chunks
from vector_store import add_chunks, add_processed_chunks
from data_processing import process_document, to_vector_store_records
from pydantic import BaseModel
from rag_service import ask_question
from vector_store import list_documents
from analysis import analyze
from data_store import load_reports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Defence Intelligence & Threat Analysis Platform",
    version="0.1.0"
)

# Allow the React frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Synthetic data for demonstration purposes only
reports = load_reports()
class AskRequest(BaseModel):
    question: str
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

    return analyze(report)


@app.post("/ask")
def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        return ask_question(request.question)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(error)}"
        )

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    allowed_extensions = {".pdf", ".txt"}

    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB."
        )

    document_id = str(uuid.uuid4())
    temp_path = Path(__file__).parent / f"temp_{document_id}{extension}"

    try:
        temp_path.write_bytes(content)

        result = process_document(str(temp_path), filename=filename)
        records = to_vector_store_records(result, document_id)

        stored_count = add_processed_chunks(
            document_id=document_id,
            records=records
        )

        return {
            "message": "Document processed and indexed successfully.",
            "document_id": document_id,
            "filename": filename,
            "date": result["date"],
            "category": result["category"],
            "page_count": result["page_count"],
            "threat_assessment": {
                "risk_score": result["risk"]["risk_score"],
                "priority": result["risk"]["priority"],
                "matched_keywords": result["risk"]["matched_keywords"],
                "negated_keywords": result["risk"]["negated_keywords"],
                "reasoning": result["risk"]["reasoning"]
            },
            "chunks_stored": stored_count
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}"
        )

    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.get("/documents")
def get_documents():
    try:
        return {
            "documents": list_documents()
        }
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve documents."
        )

