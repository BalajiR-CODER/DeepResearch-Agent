from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent import run_research

app = FastAPI(title="DeepResearch Agent")

class QueryRequest(BaseModel):
    query: str

class ReportResponse(BaseModel):
    report: str

@app.post("/research", response_model=ReportResponse)
def research_endpoint(req: QueryRequest):
    report = run_research(req.query)
    return ReportResponse(report=report)

@app.get("/")
def root():
    return {"message": "DeepResearch Agent API running"}