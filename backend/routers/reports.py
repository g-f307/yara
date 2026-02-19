"""
Reports Router
===============

POST /api/reports/pdf  — Gera PDF e retorna URL de download
POST /api/reports/docx — Gera DOCX e retorna URL de download
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile

from analysis.report_generator import ReportGenerator

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOADS_DIR = Path("uploads/reports")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class ReportSection(BaseModel):
    title: str
    content: str
    level: int = 2


class ReportRequest(BaseModel):
    project_name: str = "Análise QIIME 2"
    sections: List[ReportSection]
    output_format: str = "pdf"  # "pdf", "docx", "markdown", "html"


@router.post("/pdf")
async def generate_pdf(request: ReportRequest) -> Dict[str, Any]:
    """
    Gera relatório em PDF.
    Versão inicial — gera Markdown/HTML primeiro, PDF será implementado com ReportLab.
    """
    report = ReportGenerator(request.project_name)

    for section in request.sections:
        report.add_section(section.title, section.content, section.level)

    output_path = str(UPLOADS_DIR / "relatorio.html")
    report.generate_html(output_path)

    return {
        "data": {
            "format": "html",
            "path": output_path,
            "message": "Relatório HTML gerado. PDF com ReportLab será implementado na Fase 4.",
        },
        "plotly_spec": None,
    }


@router.post("/docx")
async def generate_docx(request: ReportRequest) -> Dict[str, Any]:
    """
    Gera relatório em DOCX.
    Versão inicial — gera Markdown primeiro, DOCX será implementado com python-docx.
    """
    report = ReportGenerator(request.project_name)

    for section in request.sections:
        report.add_section(section.title, section.content, section.level)

    output_path = str(UPLOADS_DIR / "relatorio.md")
    report.generate_markdown(output_path)

    return {
        "data": {
            "format": "markdown",
            "path": output_path,
            "message": "Relatório Markdown gerado. DOCX com python-docx será implementado na Fase 4.",
        },
        "plotly_spec": None,
    }
