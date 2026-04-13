import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyToPythonCore(req: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendUrl = process.env.PYTHON_CORE_URL || "http://localhost:8000";
  const targetUrl = new URL(`/${path.join("/")}${req.nextUrl.search}`, backendUrl);

  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("content-length");

  const res = await fetch(targetUrl, {
    method: req.method,
    headers,
    body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer(),
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  const contentType = res.headers.get("content-type");
  const contentDisposition = res.headers.get("content-disposition");

  if (contentType) responseHeaders.set("content-type", contentType);
  if (contentDisposition) responseHeaders.set("content-disposition", contentDisposition);

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
