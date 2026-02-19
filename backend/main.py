"""
YARA Python Core — FastAPI Application
=======================================

Serviço de análise científica para dados metagenômicos QIIME 2.
Expõe endpoints REST para o frontend Next.js.

Autor: Projeto YARA - IFAM
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import parse, alpha, beta, taxonomy, rarefaction, statistics, reports

app = FastAPI(
    title="YARA Python Core",
    description="Serviço de análise metagenômica para dados QIIME 2",
    version="1.0.0",
)

# CORS — permitir chamadas do frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(parse.router)
app.include_router(alpha.router)
app.include_router(beta.router)
app.include_router(taxonomy.router)
app.include_router(rarefaction.router)
app.include_router(statistics.router)
app.include_router(reports.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "yara-python-core"}
