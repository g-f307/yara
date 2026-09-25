import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { internalApiFetch } from "@/lib/internal-api-auth";
import { errorPayload, logRequest, REQUEST_ID_HEADER, requestId } from "@/lib/observability";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyToPythonCore(req: NextRequest, context: RouteContext) {
  const started = performance.now();
  const correlationId = requestId(req.headers.get(REQUEST_ID_HEADER));
  const { userId } = await auth();
  if (!userId) {
    logRequest({ requestId: correlationId, method: req.method, path: "/api/core/[...path]", status: 401, durationMs: performance.now() - started, errorCode: "AUTH_REQUIRED" });
    return NextResponse.json(errorPayload("AUTH_REQUIRED", "Autenticação necessária.", correlationId), {
      status: 401,
      headers: { "X-Request-ID": correlationId },
    });
  }

  const { path } = await context.params;
  const backendPath = `/${path.join("/")}`;
  const trackedAnalysisPaths = new Set([
    "/api/alpha/analyze",
    "/api/beta/pcoa",
    "/api/beta/distances",
    "/api/taxonomy/summary",
    "/api/taxonomy/barplot",
    "/api/rarefaction/analyze",
    "/api/statistics/compare",
    "/api/qc/summary",
  ]);
  if (req.method === "POST" && trackedAnalysisPaths.has(backendPath)) {
    return NextResponse.json(
      errorPayload("ANALYSIS_RUN_REQUIRED", "Use /api/runs para executar uma análise rastreável.", correlationId),
      { status: 409, headers: { "X-Request-ID": correlationId } },
    );
  }
  const backendUrl = process.env.PYTHON_CORE_URL || "http://localhost:8000";
  const targetUrl = new URL(`/${path.join("/")}${req.nextUrl.search}`, backendUrl);

  const headers = new Headers();
  headers.set(REQUEST_ID_HEADER, correlationId);
  for (const name of ["accept", "content-type", "range"]) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }
  const body = req.method === "GET" || req.method === "HEAD"
    ? undefined
    : await req.arrayBuffer();

  let res: Response;
  try {
    res = await internalApiFetch(targetUrl, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
    });
  } catch {
    logRequest({ requestId: correlationId, method: req.method, path: "/api/core/[...path]", status: 503, durationMs: performance.now() - started, errorCode: "BACKEND_UNAVAILABLE" });
    return NextResponse.json(errorPayload("BACKEND_UNAVAILABLE", "O serviço de análise está indisponível.", correlationId), {
      status: 503,
      headers: { "X-Request-ID": correlationId },
    });
  }

  const responseHeaders = new Headers();
  responseHeaders.set("X-Request-ID", res.headers.get(REQUEST_ID_HEADER) ?? correlationId);
  for (const name of [
    "accept-ranges",
    "cache-control",
    "content-disposition",
    "content-length",
    "content-range",
    "content-type",
  ]) {
    const value = res.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }

  let errorCode: string | null = null;
  if (!res.ok) {
    try {
      const payload = await res.clone().json();
      errorCode = payload?.error?.code ?? "INTERNAL_ERROR";
    } catch {
      errorCode = "INTERNAL_ERROR";
    }
  }
  logRequest({ requestId: correlationId, method: req.method, path: "/api/core/[...path]", status: res.status, durationMs: performance.now() - started, errorCode });
  return new NextResponse(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxyToPythonCore;
export const POST = proxyToPythonCore;
export const PUT = proxyToPythonCore;
export const PATCH = proxyToPythonCore;
export const DELETE = proxyToPythonCore;
