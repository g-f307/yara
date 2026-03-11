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
from datetime import datetime
import tempfile

from analysis.report_generator import ReportGenerator

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOADS_DIR = Path("uploads/reports")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class ReportSection(BaseModel):
    title: str
    content: str
    level: int = 2
    image_base64: Optional[str] = None


class ReportRequest(BaseModel):
    project_name: str = "Análise QIIME 2"
    sections: List[ReportSection]
    output_format: str = "pdf"  # "pdf", "docx", "markdown", "html"


@router.post("/pdf")
async def generate_pdf(request: ReportRequest) -> Dict[str, Any]:
    """
    Gera relatório em PDF nativo usando ReportLab e Pillow para converter os base64 recebidos.
    """
    report = ReportGenerator(request.project_name)

    for section in request.sections:
        report.add_section(section.title, section.content, section.level)
        if section.image_base64:
            # ReportLab deals with image handling inside ReportGenerator
            report.add_image_base64(section.image_base64, caption=f"Plot: {section.title}")

    output_path = str(UPLOADS_DIR / f"{request.project_name.replace(' ', '_')}_{int(datetime.now().timestamp())}.pdf")
    final_path = report.generate_pdf(output_path)

    return {
        "data": {
            "format": "pdf",
            "path": f"/api/reports/download/{Path(final_path).name}",
            "message": "Relatório PDF gerado com sucesso.",
        },
        "plotly_spec": None,
    }


@router.post("/docx")
async def generate_docx(request: ReportRequest) -> Dict[str, Any]:
    """
    Gera relatório em DOCX nativo usando python-docx.
    """
    report = ReportGenerator(request.project_name)

    for section in request.sections:
        report.add_section(section.title, section.content, section.level)
        if section.image_base64:
            report.add_image_base64(section.image_base64, caption=f"Plot: {section.title}")

    output_path = str(UPLOADS_DIR / f"{request.project_name.replace(' ', '_')}_{int(datetime.now().timestamp())}.docx")
    final_path = report.generate_docx(output_path)

    return {
        "data": {
            "format": "docx",
            "path": f"/api/reports/download/{Path(final_path).name}",
            "message": "Relatório DOCX gerado com sucesso.",
        },
        "plotly_spec": None,
    }

@router.get("/download/{filename}")
async def download_report(filename: str):
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        return {"error": "Arquivo não encontrado", "status": 404}
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
