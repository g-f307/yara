import { anthropic } from "@ai-sdk/anthropic";
import { streamText, tool } from "ai";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { auth } from "@clerk/nextjs/server";
import { getAlphaDiversity, getBetaDiversity, parseFile, getTaxonomy, getRarefaction } from "@/lib/actions";

export const maxDuration = 30; // max 30s Vercel limit

export async function POST(req: Request) {
    // Validate authentication
    const { userId } = await auth();
    if (!userId) {
        return new Response("Unauthorized", { status: 401 });
    }

    const { messages, projectId } = await req.json();

    if (!projectId) {
        return new Response("Missing projectId", { status: 400 });
    }

    // Define the YARA model and behavior
    const systemPrompt = `Você é o YARA (Your Assistant for Results Analysis), um especialista em bioinformática e análise metagenômica usando QIIME 2.
Responda sempre em português brasileiro de forma clara e objetiva para pesquisadores.
O usuário enviou os arquivos referentes ao projeto com ID: ${projectId}.
Use a ferramenta "parseData" se o usuário pedir para ler ou validar um arquivo do projeto.`;

    const result = streamText({
        model: anthropic("claude-3-5-sonnet-20241022"),
        system: systemPrompt,
        messages,
        tools: {
            parseData: tool({
                description: "Parse and validate a QIIME 2 file (.qzv, .tsv, etc) associated with this project.",
                parameters: z.object({
                    fileId: z.string().describe("The ID of the file to parse"),
                }),
                // @ts-ignore
                execute: async ({ fileId }: { fileId: string }) => {
                    const result = await parseFile(projectId, fileId);
                    return result;
                },
            }),
            visualizeAlphaDiversity: tool({
                description: "Request an Alpha Diversity boxplot and statistics for the dataset given a metric (shannon, simpson, chao1) and an optional metadata group column.",
                parameters: z.object({
                    metric: z.string().describe("The alpha diversity metric to use: 'shannon', 'simpson', or 'chao1'"),
                    groupCol: z.string().optional().describe("The metadata column to group by, if comparing groups"),
                }),
                // @ts-ignore
                execute: async ({ metric, groupCol }: { metric: string, groupCol?: string }) => {
                    const result = await getAlphaDiversity(projectId, metric, groupCol);
                    return { success: result.success, requested: "alpha", data: result.data || null };
                },
            }),
            visualizeBetaDiversity: tool({
                description: "Request a Beta Diversity PCoA 2D or 3D scatter plot for the dataset.",
                parameters: z.object({
                    groupCol: z.string().optional().describe("The metadata column to color the groups by"),
                }),
                // @ts-ignore
                execute: async ({ groupCol }: { groupCol?: string }) => {
                    const result = await getBetaDiversity(projectId, groupCol);
                    return { success: result.success, requested: "beta", data: result.data || null };
                }
            }),
            visualizeTaxonomy: tool({
                description: "Request a Taxonomy stacked barplot for the dataset. Shows the relative abundance of microbial taxa at a specific level.",
                parameters: z.object({
                    level: z.string().optional().describe("The taxonomic level to summarize by ('Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species'). Defaults to 'Phylum'."),
                }),
                // @ts-ignore
                execute: async ({ level }: { level?: string }) => {
                    const result = await getTaxonomy(projectId, level || "Phylum");
                    return { success: result.success, requested: "taxonomy", data: result.data || null };
                }
            }),
            visualizeRarefaction: tool({
                description: "Request a Rarefaction Curve for the dataset. Shows observed features as a function of sequencing depth to evaluate sampling sufficiency.",
                parameters: z.object({}),
                // @ts-ignore
                execute: async () => {
                    const result = await getRarefaction(projectId);
                    return { success: result.success, requested: "rarefaction", data: result.data || null };
                }
            })
        },
        async onFinish({ text, toolCalls, toolResults, finishReason, usage }) {
            // Save chat to DB Session
            try {
                const session = await prisma.analysisSession.findFirst({
                    where: { projectId },
                    orderBy: { createdAt: "desc" },
                });

                if (session) {
                    await prisma.analysisSession.update({
                        where: { id: session.id },
                        data: { messages: JSON.stringify([...messages, { role: "assistant", content: text }]) },
                    });
                } else {
                    await prisma.analysisSession.create({
                        data: {
                            projectId,
                            messages: JSON.stringify([...messages, { role: "assistant", content: text }]),
                        },
                    });
                }
            } catch (e) {
                console.error("Error saving chat session", e);
            }
        },
    });

    // Handle different versions of the AI SDK
    if (typeof (result as any).toDataStreamResponse === 'function') {
        return (result as any).toDataStreamResponse();
    } else if (typeof (result as any).toTextStreamResponse === 'function') {
        return (result as any).toTextStreamResponse();
    } else if (typeof (result as any).toAIStreamResponse === 'function') {
        return (result as any).toAIStreamResponse();
    } else {
        // Fallback for older versions
        return new Response(result.textStream, {
            headers: {
                'Content-Type': 'text/plain; charset=utf-8',
            },
        });
    }
}
