import os
from typing import List, Optional, Literal, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="DocuParse Pro API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities
ALLOWED_EXTRACT_TYPES = {
    "bank_statement": "Bank Statement Converter",
    "invoice": "Invoice Scanner",
    "receipt": "Receipt Scanner",
    "salary_slip": "Salary Slip Converter",
    "credit_card": "Credit Card Statement Converter",
    "table_extract": "Document Table Extractor",
}


def log_job(job_type: str, filename: str, size: Optional[int], status: str, summary: str, meta: Optional[dict] = None):
    try:
        from database import create_document
        from schemas import ExtractionJob
        doc = ExtractionJob(
            job_type=job_type, filename=filename, size_bytes=size, status=status, result_summary=summary, meta=meta
        )
        create_document("extractionjob", doc)
    except Exception:
        # Database is optional for this demo; ignore errors to keep API responsive
        pass


@app.get("/")
def read_root():
    return {"message": "DocuParse Pro API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from DocuParse Pro backend!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# Models
class ExtractResponse(BaseModel):
    tool: str
    filename: str
    size_bytes: Optional[int]
    content_type: Optional[str]
    summary: str
    data: Dict[str, Any]


@app.post("/api/extract/{job_type}", response_model=ExtractResponse)
async def extract_document(
    job_type: Literal[
        "bank_statement",
        "invoice",
        "receipt",
        "salary_slip",
        "credit_card",
        "table_extract",
    ],
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),
):
    if job_type not in ALLOWED_EXTRACT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported job type")

    # Read file bytes to simulate processing (not stored)
    content = await file.read()
    size = len(content)

    # Create demo outputs per tool
    demo_data: Dict[str, Any]
    if job_type == "bank_statement":
        demo_data = {
            "account_name": "Demo Account",
            "account_number": "XXXX-1234",
            "currency": "USD",
            "transactions": [
                {"date": "2025-01-04", "description": "Coffee Shop", "debit": 4.5, "credit": 0.0, "balance": 1025.5},
                {"date": "2025-01-06", "description": "Salary", "debit": 0.0, "credit": 3000.0, "balance": 4025.5},
            ],
        }
    elif job_type == "credit_card":
        demo_data = {
            "cardholder": "Demo User",
            "last4": "4242",
            "currency": "USD",
            "transactions": [
                {"date": "2025-01-03", "merchant": "Online Store", "amount": -89.99, "category": "Shopping"},
                {"date": "2025-01-07", "merchant": "Airline", "amount": -240.0, "category": "Travel"},
            ],
        }
    elif job_type == "invoice":
        demo_data = {
            "merchant": "Acme Corp",
            "invoice_number": "INV-1001",
            "issue_date": "2025-01-02",
            "due_date": "2025-01-16",
            "items": [
                {"description": "Widget A", "qty": 2, "price": 49.99, "total": 99.98},
                {"description": "Service Fee", "qty": 1, "price": 15.0, "total": 15.0},
            ],
            "subtotal": 114.98,
            "tax": 9.2,
            "grand_total": 124.18,
        }
    elif job_type == "receipt":
        demo_data = {
            "merchant": "Corner Market",
            "date": "2025-01-05",
            "items": [
                {"name": "Bananas", "qty": 3, "unit_price": 0.59, "total": 1.77},
                {"name": "Milk", "qty": 1, "unit_price": 2.49, "total": 2.49},
            ],
            "total": 4.26,
        }
    elif job_type == "salary_slip":
        demo_data = {
            "employee": "Demo Employee",
            "month": "2025-01",
            "earnings": {"basic": 2500.0, "hra": 800.0, "bonus": 200.0},
            "deductions": {"tax": 450.0, "insurance": 50.0},
            "net_pay": 3000.0,
        }
    else:  # table_extract
        demo_data = {
            "tables": [
                {
                    "name": "Table 1",
                    "columns": ["Date", "Description", "Amount"],
                    "rows": [
                        ["2025-01-01", "Opening Balance", "1000.00"],
                        ["2025-01-02", "Subscription", "-12.00"],
                    ],
                }
            ]
        }

    summary = f"Parsed {ALLOWED_EXTRACT_TYPES[job_type]} for {file.filename} (demo)"
    log_job(job_type, file.filename, size, "success", summary, {"content_type": file.content_type})

    return ExtractResponse(
        tool=ALLOWED_EXTRACT_TYPES[job_type],
        filename=file.filename,
        size_bytes=size,
        content_type=file.content_type,
        summary=summary,
        data=demo_data,
    )


@app.get("/api/jobs")
async def list_jobs(limit: int = 20):
    try:
        from database import get_documents
        docs = get_documents("extractionjob", limit=limit)
        # Convert ObjectId and datetime to strings
        def _clean(d: dict):
            out = {}
            for k, v in d.items():
                if hasattr(v, "isoformat"):
                    out[k] = v.isoformat()
                else:
                    out[k] = str(v) if k == "_id" else v
            return out
        return {"items": [_clean(doc) for doc in docs]}
    except Exception:
        return {"items": []}


# Generative AI stubs (no external calls, privacy-friendly demo)
class ChatRequest(BaseModel):
    question: str


@app.post("/api/ai/chat")
async def chat_with_pdf(req: ChatRequest):
    answer = (
        "This is a demo response. In the full version, the system would index your PDF and answer using its content.\n"
        f"Question: {req.question}\n"
        "Answer: Based on a quick scan, the document discusses totals, dates, and line items."
    )
    return {"answer": answer}


class SummarizeRequest(BaseModel):
    text: str
    max_sentences: int = 3


@app.post("/api/ai/summarize")
async def summarize(req: SummarizeRequest):
    snippet = req.text.strip().split(". ")[: req.max_sentences]
    summary = ". ".join(snippet)
    if not summary:
        summary = "No content provided."
    return {"summary": summary}


class TranslateRequest(BaseModel):
    text: str
    target_lang: str


@app.post("/api/ai/translate")
async def translate(req: TranslateRequest):
    return {"translated": f"[Translated to {req.target_lang}] {req.text}"}


class PPTRequest(BaseModel):
    text: str


@app.post("/api/ai/ppt-outline")
async def ppt_outline(req: PPTRequest):
    lines = [
        "Title: Key Insights",
        "Slide 1: Overview",
        "Slide 2: Data Tables",
        "Slide 3: Totals & Trends",
        "Slide 4: Conclusions",
    ]
    return {"outline": lines}


class ImageGenRequest(BaseModel):
    prompt: str


@app.post("/api/ai/image-gen")
async def image_gen(req: ImageGenRequest):
    # Return a placeholder image URL
    return {"image_url": "https://picsum.photos/seed/docuparse/1024/768", "prompt": req.prompt}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
