import { google } from "@ai-sdk/google";
import {
    streamText,
    tool,
    convertToModelMessages,
} from "ai";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { auth } from "@clerk/nextjs/server";
import { getAlphaDiversity, getBetaDiversity, parseFile, getTaxonomy, getRarefaction, getStatistics, getQCSummary } from "@/lib/actions";

export const maxDuration = 30; // max 30s Vercel limit

function getTextFromMessage(message: any): string {
    if (typeof message?.content === "string" && message.content) return message.content;
    if (Array.isArray(message?.parts)) {
        return message.parts
            .filter((part: any) => part.type === "text")
            .map((part: any) => part.text ?? "")
            .join("");
    }
    return "";
}

function getToolNameFromPart(part: any): string | undefined {
    if (part?.toolInvocation?.toolName) return part.toolInvocation.toolName;
    if (part?.toolName) return part.toolName;
    if (typeof part?.type === "string" && part.type.startsWith("tool-") && part.type !== "tool-invocation") {
        return part.type.replace(/^tool-/, "");
    }
    return undefined;
}

function isResolvedToolPayload(payload: any): boolean {
    return payload?.state === "result"
        || payload?.state === "output-available"
        || payload?.result != null
        || payload?.output != null;
}

function unwrapToolResult(result: any): any {
    if (result && typeof result === "object" && "type" in result && "value" in result && !result.success) {
        if (typeof result.value === "string") {
            try {
                return JSON.parse(result.value);
            } catch {
                return result.value;
            }
        }
        return result.value;
    }
    return result;
}

function summarizeToolResult(result: any): any {
    const unwrapped = unwrapToolResult(result);
    if (!unwrapped || typeof unwrapped !== "object") return unwrapped;

    return {
        success: unwrapped.success,
        requested: unwrapped.requested,
        error: unwrapped.error,
        data: unwrapped.data ?? unwrapped.stats ?? unwrapped.plotly_spec?._stats ?? null,
        plotTitle: unwrapped.plotly_spec?.layout?.title ?? unwrapped.data?.layout?.title ?? null,
    };
}

function getRequestedToolNames(text: string): Set<string> {
    if (text.trim().startsWith("[Sistema]")) return new Set();

    const normalized = text
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");

    const requested = new Set<string>();

    if (/\b(alpha|alfa|shannon|simpson|chao1|faith|pielou|diversidade alfa)\b/.test(normalized)) {
        requested.add("visualizeAlphaDiversity");
    }
    if (/\b(beta|pcoa|bray|jaccard|ordinacao|ordenacao|distancia|distancias)\b/.test(normalized)) {
        requested.add("visualizeBetaDiversity");
    }
    if (/\b(taxonomia|taxonomica|taxonomico|taxon|taxa|barplot|composicao)\b/.test(normalized)) {
        requested.add("visualizeTaxonomy");
    }
    if (/\b(rarefacao|rarefaction|rarefa[cç]ao|curva de rarefacao|profundidade)\b/.test(normalized)) {
        requested.add("visualizeRarefaction");
    }
    if (/\b(estatistica|estatistico|kruskal|mann|whitney|p-value|p valor|significancia|compare|comparar|comparacao|grupos)\b/.test(normalized)) {
        requested.add("visualizeStatistics");
    }
    if (/\b(parse|parsear|validar|valide|carregar|processar arquivo)\b/.test(normalized)) {
        requested.add("parseData");
    }
    if (/\b(qc|qualidade|controle de qualidade|reads|sequenciamento|cobertura|profundidade de sequenciamento)\b/.test(normalized)) {
        requested.add("analyzeQuality");
    }

    return requested;
}

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

    // systemPrompt will be built after messages are parsed so we can inject resolvedToolNames
    let systemPrompt = '';
    // Build the set of resolved toolCallIds AND their tool names.
    // The client sends UIMessages (not CoreMessages), so tool results are embedded as
    // toolInvocations[].state === 'result' inside assistant messages — NOT as role:'tool' messages.
    const resolvedToolIds = new Set<string>();
    const resolvedToolNames = new Set<string>(); // track names for system prompt injection
    messages.forEach((m: any) => {
        // UIMessage format: toolInvocations on assistant messages
        if (m.role === 'assistant' && Array.isArray(m.toolInvocations)) {
            m.toolInvocations.forEach((ti: any) => {
                if (isResolvedToolPayload(ti)) {
                    if (ti.toolCallId) resolvedToolIds.add(ti.toolCallId);
                    if (ti.toolName) resolvedToolNames.add(ti.toolName);
                }
            });
        }
        // UIMessage parts format: tool-invocation parts with state 'result'
        if (m.role === 'assistant' && Array.isArray(m.parts)) {
            m.parts.forEach((p: any) => {
                if (p.type === 'tool-invocation' && p.toolInvocation) {
                    const ti = p.toolInvocation;
                    if (isResolvedToolPayload(ti)) {
                        if (ti.toolCallId) resolvedToolIds.add(ti.toolCallId);
                        if (ti.toolName) resolvedToolNames.add(ti.toolName);
                    }
                }
                // Persisted flat format: type 'tool-{toolName}'
                if (p.type?.startsWith('tool-') && p.type !== 'tool-invocation') {
                    if (isResolvedToolPayload(p)) {
                        if (p.toolCallId) resolvedToolIds.add(p.toolCallId);
                        const toolName = getToolNameFromPart(p);
                        if (toolName) resolvedToolNames.add(toolName);
                    }
                }
                if (p.type === 'dynamic-tool' && isResolvedToolPayload(p)) {
                    if (p.toolCallId) resolvedToolIds.add(p.toolCallId);
                    const toolName = getToolNameFromPart(p);
                    if (toolName) resolvedToolNames.add(toolName);
                }
            });
        }
        // Legacy CoreMessage format fallback (role:'tool')
        if (m.role === 'tool' && Array.isArray(m.content)) {
            m.content.forEach((c: any) => {
                if (c.type === 'tool-result' && c.toolCallId) {
                    resolvedToolIds.add(c.toolCallId);
                }
            });
        }
    });

    const lastUserMessage = [...messages].reverse().find((m: any) => m.role === "user");
    const lastUserText = getTextFromMessage(lastUserMessage);
    const isSystemInstruction = lastUserText.trim().startsWith("[Sistema]");
    const requestedToolNames = getRequestedToolNames(lastUserText);
    let analysisHistory = "";

    try {
        const summaries = await (prisma as any).analysisSummary.findMany({
            where: { projectId },
            orderBy: { createdAt: "desc" },
            take: 10,
        });

        if (summaries.length > 0) {
            analysisHistory = `\n\nANÁLISES JÁ REALIZADAS NESTE PROJETO:\n${summaries.map((summary: any) =>
                `- ${summary.type.toUpperCase()} (${summary.createdAt.toLocaleDateString("pt-BR")}): métrica=${summary.metric ?? "N/A"}, grupo=${summary.groupCol ?? "sem grupo"}`
            ).join("\n")}`;
        }
    } catch (error) {
        console.warn("AnalysisSummary is not available yet.", error);
    }

    // Build the system prompt now that we know which tools have already been called
    const alreadyCalledSection = resolvedToolNames.size > 0
        ? `\n\nFERRAMENTAS JÁ EXECUTADAS NESTA SESSÃO (NÃO REPITA):\n${[...resolvedToolNames].map(n => `- ${n}`).join('\n')}\nNão chame nenhuma dessas ferramentas novamente, a menos que o usuário peça explicitamente para refazer a análise.`
        : '';

    systemPrompt = `Você é o YARA (Your Assistant for Results Analysis), um especialista em bioinformática e análise metagenômica 16S rRNA utilizando QIIME 2. Responda SEMPRE em português brasileiro.

CAPACIDADES:
Você pode gerar as seguintes visualizações chamando as ferramentas disponíveis:
- visualizeAlphaDiversity: boxplot de diversidade alfa (Shannon, Simpson, Chao1)
- visualizeBetaDiversity: PCoA de diversidade beta (Bray-Curtis)
- visualizeTaxonomy: gráfico de barras de composição taxonômica
- visualizeRarefaction: curvas de rarefação por amostra
- visualizeStatistics: testes estatísticos não-paramétricos entre grupos
- parseData: valida/parseia arquivos QIIME2 do projeto
- analyzeQuality: painel de QC com reads por amostra e outliers de cobertura

REGRAS OBRIGATÓRIAS:
1. Quando o usuário pedir um gráfico, SEMPRE chame a ferramenta correspondente. Nunca apenas descreva o gráfico ou diga que "está gerando" sem chamar a ferramenta.
2. Chame APENAS a(s) ferramenta(s) que o usuário explicitamente solicitou. Não adicione gráficos extras não pedidos.
3. Se a ferramenta retornar success:true, confirme que o gráfico foi gerado e descreva brevemente o resultado.
4. Se a ferramenta retornar success:false, informe o erro ao usuário e sugira o que tentar.
5. Seja objetivo e científico. Não especule sobre resultados sem dados.
6. Se receber uma mensagem iniciada com [Sistema], responda somente com orientação textual curta. Não chame ferramentas nesse caso.

O usuário enviou arquivos ao projeto com ID: ${projectId}.${alreadyCalledSection}${analysisHistory}`;


    // Resolved ones must be preserved so the model knows what was already done.
    const sanitizedMessages = messages.map((m: any) => {
        if (m.role === 'assistant') {
            const cleanMsg = { ...m };

            if (Array.isArray(cleanMsg.toolInvocations)) {
                // Keep resolved, drop pending (unresolved would cause AI_MissingToolResultsError)
                cleanMsg.toolInvocations = cleanMsg.toolInvocations.filter(
                    (ti: any) => ti.state === 'result' || ti.result != null
                );
            }

            if (Array.isArray(cleanMsg.parts)) {
                cleanMsg.parts = cleanMsg.parts.filter((p: any) => {
                    if (p.type === 'tool-invocation' && p.toolInvocation) {
                        const ti = p.toolInvocation;
                        return ti.state === 'result' || ti.result != null;
                    }
                    if (p.type === 'tool-call') {
                        return resolvedToolIds.has(p.toolCallId);
                    }
                    if (p.type?.startsWith('tool-') && p.type !== 'tool-invocation' && p.type !== 'tool-result') {
                        return p.state === 'result' || p.result != null;
                    }
                    return true;
                });

                // If all parts were stripped, fall back to text only
                if (cleanMsg.parts.length === 0) {
                    cleanMsg.parts = [{ type: 'text', text: cleanMsg.content || '' }];
                }
            }

            return cleanMsg;
        }
        return m;
    }).filter((m: any) => m.role !== 'tool');

    // Before converting to model messages, strip previous tool payloads entirely.
    // Old toolInvocations/tool parts can be re-hydrated by the UI stream on the next turn,
    // which makes prior graphs appear in the new assistant bubble.
    const messagesForModel = sanitizedMessages.map((m: any) => {
        if (m.role === 'assistant') {
            const text = getTextFromMessage(m);

            return {
                id: m.id,
                role: m.role,
                content: text,
                parts: [{ type: 'text', text }],
            };
        }
        return m;
    });

    try {
        const allTools = {
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
            }),
            visualizeStatistics: tool({
                    description: "Executa teste estatístico não-paramétrico comparando uma métrica de diversidade alfa entre grupos. Use para p-value, significância, Kruskal-Wallis ou Mann-Whitney.",
                    parameters: z.object({
                        groupCol: z.string().optional().describe("Coluna de metadados com os grupos, por exemplo 'Grupo' ou 'Tratamento'. Se o usuário não especificar, omita e o backend tentará inferir."),
                        metricCol: z.string().optional().describe("Métrica a comparar, por exemplo 'shannon', 'simpson', 'chao1' ou 'observed_features'. Se o usuário não especificar, omita para usar 'shannon' quando disponível."),
                        test: z.enum(["kruskal", "mann_whitney"]).default("kruskal").describe("Use 'kruskal' para 3+ grupos e 'mann_whitney' para exatamente 2 grupos."),
                        group1: z.string().optional().describe("Primeiro grupo, apenas para Mann-Whitney."),
                        group2: z.string().optional().describe("Segundo grupo, apenas para Mann-Whitney."),
                    }),
                    // @ts-ignore
                    execute: async ({ groupCol, metricCol, test, group1, group2 }: { groupCol?: string, metricCol?: string, test: "kruskal" | "mann_whitney", group1?: string, group2?: string }) => {
                        try {
                            const res = await getStatistics(projectId, groupCol, metricCol, test || "kruskal", group1, group2);
                            if (!res.success) {
                                return { success: false, error: res.error || "Failed to generate Statistics plot.", requested: "statistics" };
                            }
                            return { success: true, requested: "statistics", plotly_spec: res.data || null };
                        } catch (e: any) {
                            return { success: false, error: e.message || "Unknown error generating Statistics plot.", requested: "statistics" };
                        }
                    }
            })
            ,
            analyzeQuality: tool({
                    description: "Gera um painel de controle de qualidade de sequenciamento (QC), com reads por amostra e detecção de outliers de cobertura.",
                    parameters: z.object({}),
                    // @ts-ignore
                    execute: async () => {
                        try {
                            const res = await getQCSummary(projectId);
                            if (!res.success) {
                                return { success: false, error: res.error || "Failed to generate QC summary.", requested: "qc" };
                            }
                            return { success: true, requested: "qc", plotly_spec: res.data || null, stats: res.stats || null };
                        } catch (e: any) {
                            return { success: false, error: e.message || "Unknown error generating QC summary.", requested: "qc" };
                        }
                    }
            })
        };

        const activeTools = isSystemInstruction
            ? {}
            : Object.fromEntries(
                Object.entries(allTools).filter(([name]) => {
                    if (requestedToolNames.size > 0) return requestedToolNames.has(name);
                    return name === "parseData" || !resolvedToolNames.has(name);
                })
            );

        const result = streamText({
            model: google("gemini-2.5-flash-lite"),
            system: systemPrompt,
            messages: await convertToModelMessages(messagesForModel),
            tools: activeTools,
            async onFinish({ response }) {
                // Save chat to DB Session
                try {
                    const session = await prisma.analysisSession.findFirst({
                        where: { projectId },
                        orderBy: { createdAt: "desc" },
                    });

                    // Build a map of toolCallId -> result from role:'tool' messages in response
                    // response.messages is ModelMessage[] — tool results live in role:'tool' entries
                    const toolResultMap = new Map<string, any>();
                    for (const rm of response.messages) {
                        if (rm.role === 'tool' && Array.isArray(rm.content)) {
                            for (const block of rm.content) {
                                if (block.type === 'tool-result') {
                                    toolResultMap.set(block.toolCallId, block.output);
                                }
                            }
                        }
                    }

                    // Helper: extract plain text from a UIMessage (AI SDK v6 stores it in parts, not content)
                    const extractUserText = (m: any): string => {
                        if (Array.isArray(m.parts)) {
                            const t = m.parts.find((p: any) => p.type === 'text');
                            if (t?.text) return t.text;
                        }
                        return typeof m.content === 'string' ? m.content : '';
                    };

                    // Helper: serialize an incoming request UIMessage for storage
                    const serializeRequestMessage = (m: any) => {
                        if (m.role === 'user') {
                            const text = extractUserText(m);
                            return {
                                id: m.id,
                                role: 'user' as const,
                                content: text,
                                parts: [{ type: 'text', text }],
                            };
                        }
                        // assistant messages from the request are already-stored history — pass through
                        return {
                            id: m.id,
                            role: m.role,
                            content: typeof m.content === 'string' ? m.content : '',
                            parts: m.parts || [],
                            toolInvocations: m.toolInvocations || [],
                        };
                    };

                    // Save only the NEW user message from this turn (the last user message in the request).
                    // Historical messages are already stored correctly in the DB and will be preserved
                    // by the allMessagesMap merge. Re-serializing them here would overwrite the correct
                    // DB format (tool-{toolName} flat) with the client streaming format (tool-invocation).
                    const lastUserMsg = [...messages].reverse().find((m: any) => m.role === 'user');
                    const incomingMessages = lastUserMsg ? [serializeRequestMessage(lastUserMsg)] : [];

                    // Build ONE merged assistant message from ALL assistant entries in response.messages.
                    // streamText with tools produces multiple assistant messages per turn
                    // (pre-tool with tool-call blocks, post-tool with final text), each with a different ID.
                    // Saving them separately causes duplicates because the client (useChat) only knows
                    // the LAST assistant message's ID. The earlier "ghost" messages accumulate each turn.
                    const responseAssistants = response.messages.filter((m: any) => m.role === 'assistant');
                    const lastAsst = responseAssistants[responseAssistants.length - 1];

                    const responseMessages: any[] = [];
                    if (lastAsst) {
                        // Use the LAST assistant's ID — this is what useChat tracks on the client
                        // Cast to any: ResponseMessage type doesn't expose 'id' statically but it exists at runtime
                        const finalId = (lastAsst as any).id || `ai-${Date.now()}-${Math.random()}`;

                        // Collect ALL content blocks from ALL assistant messages in the response
                        const allContentBlocks: any[] = responseAssistants.flatMap((m: any) =>
                            Array.isArray(m.content) ? m.content : []
                        );

                        // Use the LAST text block as the final response text
                        const textBlocks = allContentBlocks.filter((b: any) => b.type === 'text');
                        const textContent = textBlocks[textBlocks.length - 1]?.text || '';

                        const toolInvocations: any[] = [];
                        const parts: any[] = textContent ? [{ type: 'text', text: textContent }] : [];

                        for (const block of allContentBlocks) {
                            if (block.type === 'tool-call') {
                                if (!Object.prototype.hasOwnProperty.call(activeTools, block.toolName)) continue;

                                // Skip tools that were already called in PREVIOUS turns.
                                // The model (Gemini Lite) sometimes re-calls old tools despite instructions.
                                // Filtering here ensures each response message only contains NEW tool calls.
                                if (requestedToolNames.size === 0 && resolvedToolNames.has(block.toolName)) continue;

                                const result = toolResultMap.get(block.toolCallId);
                                toolInvocations.push({
                                    state: 'result',
                                    toolCallId: block.toolCallId,
                                    toolName: block.toolName,
                                    args: block.args ?? block.input,
                                    result: result ?? { success: false, error: 'Resultado não disponível.' },
                                });
                                parts.push({
                                    type: `tool-${block.toolName}`,
                                    toolCallId: block.toolCallId,
                                    toolName: block.toolName,
                                    args: block.args ?? block.input,
                                    state: 'result',
                                    result: result ?? { success: false, error: 'Resultado não disponível.' },
                                });
                            }
                        }

                        responseMessages.push({ id: finalId, role: 'assistant', content: textContent, parts, toolInvocations });
                    }

                    const currentTurnMessages = [...incomingMessages, ...responseMessages];

                    const typeMap: Record<string, string> = {
                        visualizeAlphaDiversity: "alpha",
                        visualizeBetaDiversity: "beta",
                        visualizeTaxonomy: "taxonomy",
                        visualizeRarefaction: "rarefaction",
                        visualizeStatistics: "statistics",
                        analyzeQuality: "qc",
                    };

                    for (const assistantMessage of responseMessages) {
                        for (const invocation of assistantMessage.toolInvocations ?? []) {
                            const analysisType = typeMap[invocation.toolName];
                            const result = unwrapToolResult(invocation.result);
                            if (!analysisType || !result?.success) continue;

                            try {
                                await (prisma as any).analysisSummary.create({
                                    data: {
                                        projectId,
                                        type: analysisType,
                                        metric: invocation.args?.metric ?? invocation.args?.metricCol ?? invocation.args?.level ?? null,
                                        groupCol: invocation.args?.groupCol ?? null,
                                        resultJson: summarizeToolResult(result),
                                    },
                                });
                            } catch (error) {
                                console.warn("Could not save AnalysisSummary.", error);
                            }
                        }
                    }

                    if (session) {
                        const previousMessages = JSON.parse(session.messages as string || "[]");
                        const allMessagesMap = new Map();
                        previousMessages.forEach((m: any) => allMessagesMap.set(m.id, m));
                        currentTurnMessages.forEach((m: any) => allMessagesMap.set(m.id, m));
                        await prisma.analysisSession.update({
                            where: { id: session.id },
                            data: { messages: JSON.stringify(Array.from(allMessagesMap.values())) },
                        });
                    } else {
                        await prisma.analysisSession.create({
                            data: { projectId, messages: JSON.stringify(currentTurnMessages) },
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
