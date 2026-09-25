import { NextRequest, NextResponse } from "next/server";
import { getProjectAnalysisRun } from "@/lib/actions";

export const runtime = "nodejs";

export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const projectId = request.nextUrl.searchParams.get("project_id");
  if (!projectId) return NextResponse.json({ error: "project_id é obrigatório." }, { status: 400 });
  const { id } = await context.params;
  const result = await getProjectAnalysisRun(projectId, id);
  return NextResponse.json(result, { status: result.success ? 200 : 404 });
}
