import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { internalApiFetch } from "@/lib/internal-api-auth";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyToPythonCore(req: NextRequest, context: RouteContext) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json(
      { error: "Autenticação necessária." },
      { status: 401 },
    );
  }

  const { path } = await context.params;
  const backendUrl = process.env.PYTHON_CORE_URL || "http://localhost:8000";
  const targetUrl = new URL(`/${path.join("/")}${req.nextUrl.search}`, backendUrl);

  const headers = new Headers();
  for (const name of ["accept", "content-type", "range"]) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }
  const body = req.method === "GET" || req.method === "HEAD"
    ? undefined
    : await req.arrayBuffer();

  const res = await internalApiFetch(targetUrl, {
    method: req.method,
    headers,
    body,
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  const contentType = res.headers.get("content-type");
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
