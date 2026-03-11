import { google } from "@ai-sdk/google";
import {
    streamText,
    tool,
    convertToModelMessages,
} from "ai";
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

    // Find all toolCallIds that actually have a resolved 'tool' message in the history
    const resolvedToolIds = new Set<string>();
    messages.forEach((m: any) => {
        if (m.role === 'tool' && Array.isArray(m.content)) {
            m.content.forEach((c: any) => {
                if (c.type === 'tool-result' && c.toolCallId) {
                    resolvedToolIds.add(c.toolCallId);
                }
            });
        }
    });

    // Sanitize the history to drop toolInvocations that lack a corresponding tool result
    // This strictly prevents the AI_MissingToolResultsError that crashes the chat
    const sanitizedMessages = messages.map((m: any) => {
        if (m.role === 'assistant') {
            const cleanMsg = { ...m };
            
            if (cleanMsg.toolInvocations) {
                const validTools = cleanMsg.toolInvocations.filter((ti: any) => resolvedToolIds.has(ti.toolCallId));
                if (validTools.length === 0) {
                    delete cleanMsg.toolInvocations;
                } else {
                    cleanMsg.toolInvocations = validTools;
                }
            }

            if (Array.isArray(cleanMsg.parts)) {
                cleanMsg.parts = cleanMsg.parts.filter((p: any) => {
                    if (p.type === 'tool-invocation' && p.toolInvocation) {
                        return resolvedToolIds.has(p.toolInvocation.toolCallId);
                    }
                    if (p.type === 'tool-call') {
                        return resolvedToolIds.has(p.toolCallId);
                    }
                    if (p.type?.startsWith('tool-') && p.type !== 'tool-call' && p.type !== 'tool-result') {
                        return resolvedToolIds.has(p.toolCallId);
                    }
                    return true;
                });
                
                // If we stripped all parts, ensure it has at least a text fallback
                if (cleanMsg.parts.length === 0) {
                    cleanMsg.parts = [{ type: 'text', text: cleanMsg.content || '' }];
                }
            }
            
            return cleanMsg;
        }
        return m;
    });

    try {
        const result = streamText({
            model: google("gemini-2.5-flash"),
            system: systemPrompt,
            // convertToModelMessages converts UIMessage[] → ModelMessage[] (AI SDK v6 API)
            messages: await convertToModelMessages(sanitizedMessages),
            tools: {
            parseData: tool({
                description: "Parse and validate a QIIME 2 file (.qzv, .tsv, etc) associated with this project.",
                parameters: z.object({
                    fileId: z.string().describe("The ID of the file to parse"),
                }),
                // @ts-ignore
                execute: async ({ fileId }: { fileId: string }) => {
                    const res = await parseFile(projectId, fileId);
                    return res;
                },
            }),
            visualizeAlphaDiversity: tool({
                description: "Request an Alpha Diversity boxplot and statistics for the dataset given a metric (shannon, simpson, chao1) and an optional metadata group column. IMPORTANT: Always default to 'shannon' unless the user specifically asks for another metric.",
                parameters: z.object({
                    metric: z.string().describe("The alpha diversity metric to use: 'shannon', 'simpson', or 'chao1'. Default is 'shannon'."),
                    groupCol: z.string().optional().describe("The metadata column to group by, if comparing groups"),
                }),
                // @ts-ignore
                execute: async ({ metric, groupCol }: { metric: string, groupCol?: string }) => {
                    try {
                        const res = await getAlphaDiversity(projectId, metric || "shannon", groupCol);
                        if (!res.success) {
                            return { success: false, error: res.error || "Failed to generate plot. The requested metric may not exist in this dataset.", requested: "alpha" };
                        }
                        return { success: true, requested: "alpha", plotly_spec: res.data || null };
                    } catch (e: any) {
                        return { success: false, error: e.message || "Unknown error generating Alpha Diversity plot.", requested: "alpha" };
                    }
                },
            }),
            visualizeBetaDiversity: tool({
                description: "Request a Beta Diversity PCoA 2D or 3D scatter plot for the dataset.",
                parameters: z.object({
                    groupCol: z.string().optional().describe("The metadata column to color the groups by"),
                }),
                // @ts-ignore
                execute: async ({ groupCol }: { groupCol?: string }) => {
                    try {
                        const res = await getBetaDiversity(projectId, groupCol);
                        if (!res.success) {
                            return { success: false, error: res.error || "Failed to generate Beta Diversity plot.", requested: "beta" };
                        }
                        return { success: true, requested: "beta", plotly_spec: res.data || null };
                    } catch (e: any) {
                        return { success: false, error: e.message || "Unknown error generating Beta Diversity plot.", requested: "beta" };
                    }
                }
            }),
            visualizeTaxonomy: tool({
                description: "Request a Taxonomy stacked barplot for the dataset. Shows the relative abundance of microbial taxa at a specific level.",
                parameters: z.object({
                    level: z.string().optional().describe("The taxonomic level to summarize by ('Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species'). Defaults to 'Phylum'."),
                }),
                // @ts-ignore
                execute: async ({ level }: { level?: string }) => {
                    try {
                        const res = await getTaxonomy(projectId, level || "Phylum");
                        if (!res.success) {
                            return { success: false, error: res.error || "Failed to generate Taxonomy plot.", requested: "taxonomy" };
                        }
                        return { success: true, requested: "taxonomy", plotly_spec: res.data || null };
                    } catch (e: any) {
                        return { success: false, error: e.message || "Unknown error generating Taxonomy plot.", requested: "taxonomy" };
                    }
                }
            }),
            visualizeRarefaction: tool({
                description: "Request a Rarefaction Curve for the dataset. Shows observed features as a function of sequencing depth to evaluate sampling sufficiency.",
                parameters: z.object({}),
                // @ts-ignore
                execute: async () => {
                    try {
                        const res = await getRarefaction(projectId);
                        if (!res.success) {
                            return { success: false, error: res.error || "Failed to generate Rarefaction plot.", requested: "rarefaction" };
                        }
                        return { success: true, requested: "rarefaction", plotly_spec: res.data || null };
                    } catch (e: any) {
                        return { success: false, error: e.message || "Unknown error generating Rarefaction curve.", requested: "rarefaction" };
                    }
                }
            })
        },
        async onFinish({ response }) {
            // Save chat to DB Session
            try {
                const session = await prisma.analysisSession.findFirst({
                    where: { projectId },
                    orderBy: { createdAt: "desc" },
                });

                if (session) {
                    const previousMessages = JSON.parse(session.messages as string || "[]");

                    const allMessagesMap = new Map();
                    previousMessages.forEach((m: any) => allMessagesMap.set(m.id, m));
                    messages.forEach((m: any) => {
                        if (m.id) allMessagesMap.set(m.id, m);
                    });
                    response.messages.forEach((m: any) => {
                        const mId = m.id || `ai-${Date.now()}-${Math.random()}`;
                        allMessagesMap.set(mId, { ...m, id: mId });
                    });

                    await prisma.analysisSession.update({
                        where: { id: session.id },
                        data: { messages: JSON.stringify(Array.from(allMessagesMap.values())) },
                    });
                } else {
                    await prisma.analysisSession.create({
                        data: {
                            projectId,
                            messages: JSON.stringify([...messages, ...response.messages]),
                        },
                    });
                }
            } catch (e) {
                console.error("Error saving chat session", e);
            }
        },
    });

    // toUIMessageStreamResponse() is the correct method for AI SDK v6 + DefaultChatTransport
    // It returns a Response with the UI message stream format that useChat expects
    return result.toUIMessageStreamResponse();
} catch (e: any) {
        console.error("FATAL ERROR IN AI CHAT STREAM:", e);
        return new Response(e.message || "Failed to create stream", { status: 500 });
    }
}
