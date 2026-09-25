import { NextRequest, NextResponse } from "next/server";
import { ANALYSIS_METHODS, type AnalysisMethod } from "@/lib/analysis-runs";
import { getProjectAnalysisRuns, requestProjectAnalysis } from "@/lib/actions";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const projectId = request.nextUrl.searchParams.get("project_id");
  if (!projectId) return NextResponse.json({ error: "project_id é obrigatório." }, { status: 400 });
  const result = await getProjectAnalysisRuns(projectId);
  return NextResponse.json(result, { status: result.success ? 200 : 404 });
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (!body?.project_id || !ANALYSIS_METHODS.includes(body.method as AnalysisMethod)) {
    return NextResponse.json({ error: "project_id e um método válido são obrigatórios." }, { status: 400 });
  }
  const result = await requestProjectAnalysis(body.project_id, body.method, body.parameters ?? {});
  return NextResponse.json(result, { status: result.success ? 201 : 422 });
}
