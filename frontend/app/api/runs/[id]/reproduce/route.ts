import { NextRequest, NextResponse } from "next/server";
import { reproduceProjectAnalysis } from "@/lib/actions";

export const runtime = "nodejs";

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const body = await request.json().catch(() => null);
  if (!body?.project_id) return NextResponse.json({ error: "project_id é obrigatório." }, { status: 400 });
  const { id } = await context.params;
  const result = await reproduceProjectAnalysis(body.project_id, id, body.parameters);
  return NextResponse.json(result, { status: result.success ? 201 : 422 });
}
