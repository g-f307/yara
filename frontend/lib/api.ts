/**
 * YARA API Client
 * ================
 * Cliente para comunicação com o python-core (FastAPI).
 *
 * Usa NEXT_PUBLIC_PYTHON_CORE_URL em produção (Docker)
 * e fallback para localhost:8000 em desenvolvimento.
 */

const isServer = typeof window === "undefined";
const API_BASE = isServer
    ? (process.env.PYTHON_CORE_URL ?? "http://localhost:8000")
    : "/api/core";

interface ApiResponse<T = unknown> {
    data: T;
    plotly_spec: Record<string, unknown> | null;
}

async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<ApiResponse<T>> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    if (!res.ok) {
        const body = await res.text();
        throw new Error(`API ${res.status}: ${body}`);
    }

    return res.json() as Promise<ApiResponse<T>>;
}

// ── Endpoints ──────────────────────────────────────

export async function healthCheck() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
}

export async function analyzeAlpha(
    data: Record<string, unknown>[],
    metric = "shannon",
    groupCol?: string
) {
    return request("/api/alpha/analyze", {
        method: "POST",
        body: JSON.stringify({ data, metric, group_col: groupCol }),
    });
}

export async function computePCoA(
    distanceMatrix: number[][],
    sampleIds: string[],
    metadata?: Record<string, unknown>[],
    groupCol?: string
) {
    return request("/api/beta/pcoa", {
        method: "POST",
        body: JSON.stringify({
            distance_matrix: distanceMatrix,
            sample_ids: sampleIds,
            metadata,
            group_col: groupCol,
        }),
    });
}

export async function getDistances(
    distanceMatrix: number[][],
    sampleIds: string[]
) {
    return request("/api/beta/distances", {
        method: "POST",
        body: JSON.stringify({
            distance_matrix: distanceMatrix,
            sample_ids: sampleIds,
        }),
    });
}

export async function taxonomySummary(
    data: Record<string, unknown>[],
    level = "Phylum",
    topN = 10
) {
    return request("/api/taxonomy/summary", {
        method: "POST",
        body: JSON.stringify({ data, level, top_n: topN }),
    });
}

export async function taxonomyBarplot(
    data: Record<string, unknown>[],
    level = "Phylum",
    topN = 10
) {
    return request("/api/taxonomy/barplot", {
        method: "POST",
        body: JSON.stringify({ data, level, top_n: topN }),
    });
}

export async function analyzeRarefaction(
    data: Record<string, unknown>[],
    maxSamples = 20
) {
    return request("/api/rarefaction/analyze", {
        method: "POST",
        body: JSON.stringify({ data, max_samples: maxSamples }),
    });
}

export async function compareStatistics(
    data: Record<string, unknown>[],
    groupCol: string,
    metricCol: string,
    test: "kruskal" | "mann_whitney" = "kruskal",
    group1?: string,
    group2?: string
) {
    return request("/api/statistics/compare", {
        method: "POST",
        body: JSON.stringify({
            data,
            group_col: groupCol,
            metric_col: metricCol,
            test,
            group1,
            group2,
        }),
    });
}

export async function generateReport(
    sections: { title: string; content: string; level?: number }[],
    projectName = "Análise QIIME 2",
    format: "pdf" | "docx" = "pdf"
) {
    return request(`/api/reports/${format}`, {
        method: "POST",
        body: JSON.stringify({
            project_name: projectName,
            sections,
            output_format: format,
        }),
    });
}
