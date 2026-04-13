"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Paperclip, Microscope } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

import { DnaIcon } from "@/components/yara-logo"
import { AnalysisCard } from "@/components/analysis-card"
import { FileUpload } from "@/components/file-upload"
import {
  mockMessages,
  suggestionChips,
  type ChatMessage,
} from "@/lib/mock-data"

import { Suspense } from "react"
import { PlotlyPlot } from "@/components/plots/plotly-plot"
import { getFriendlyError } from "@/lib/error-messages"

import { useResultsStore } from "@/store/use-results-store"

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

function getRequestedToolNames(text: string): Set<string> {
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

  return requested;
}

function MessageBubble({ message, allowedToolNames }: { message: any; allowedToolNames?: Set<string> }) {
  const isUser = message.role === "user"

  // Unified data access for historical (DB) and active stream messages
  const textContent = getTextFromMessage(message);

  // Merge toolInvocations (from history DB format) and parts (from stream format)
  const toolInvocations = message.toolInvocations || [];
  const parts = message.parts || [];

  // AI SDK v6 emits parts with type 'tool-invocation' where actual data is nested
  // inside p.toolInvocation. Older/persisted parts use type 'tool-{toolName}' with flat structure.
  const streamToolParts = parts
    .filter((p: any) => p.type?.startsWith("tool-") || p.type === "dynamic-tool")
    .map((p: any, idx: number) => {
      // AI SDK v6 streaming format: { type: 'tool-invocation', toolInvocation: { toolCallId, toolName, state, result, args } }
      if (p.type === "tool-invocation" && p.toolInvocation) {
        const ti = p.toolInvocation;
        const isFinished = ti.state === "result" || ti.state === "output-available" || !!ti.result;
        return {
          toolCallId: ti.toolCallId,
          toolName: ti.toolName,
          state: isFinished ? "result" : "call",
          result: ti.result ?? ti.output,
          args: ti.args ?? ti.input,
        };
      }
      // Persisted / legacy flat format: { type: 'tool-{toolName}', toolCallId, toolName, state, result, args }
      return {
        toolCallId: p.toolCallId || p.toolName || `tool-fallback-${idx}`,
        toolName: p.toolName ?? p.type?.replace(/^tool-/, ""),
        state: p.state === "output-available" || p.output || p.result ? "result" : "call",
        result: p.output || p.result,
        args: p.args || p.input,
      };
    });

  const allToolsMap = new Map();
  [...toolInvocations, ...streamToolParts].forEach((t: any) => {
    if (!allToolsMap.has(t.toolCallId)) {
      allToolsMap.set(t.toolCallId, t);
    } else if (t.state === 'result' || t.result) {
      allToolsMap.set(t.toolCallId, t); // Prefer populated result
    }
  });
  const mergedTools = Array.from(allToolsMap.values()).filter(
    (tool: any) => !allowedToolNames || allowedToolNames.size === 0 || allowedToolNames.has(tool.toolName)
  );

  const setPlotData = useResultsStore((state: any) => state.setPlotData);
  const activeTab = useResultsStore((state: any) => state.activeTab);

  // Auto-sync valid finished tools to the global Results Store
  useEffect(() => {
    if (isUser) return;

    // Use a timeout to ensure the DOM and internal stream states have settled
    const timeoutId = setTimeout(() => {
      mergedTools.forEach((tool: any) => {
        const isFinished = tool.state === "result" || !!tool.result;
        let result = tool.result || tool.output;

        // Unwrap React Server Component ({type, value}) serialization proxy for the store
        if (result && typeof result === "object" && "type" in result && "value" in result && !result.plotly_spec) {
          let val = result.value;
          if (typeof val === "string") {
            try { val = JSON.parse(val); } catch (e) {}
          }
          result = val;
        }
        
        if (isFinished && result && (result.plotly_spec || result.data?.data)) {
          // Both `plotly_spec` and `result.data` structures handled
          const spec = result.plotly_spec || result.data;
          
          if (tool.toolName === "visualizeAlphaDiversity") {
            setPlotData('alpha', spec);
          } else if (tool.toolName === "visualizeBetaDiversity") {
            setPlotData('beta', spec);
          } else if (tool.toolName === "visualizeTaxonomy") {
            setPlotData('taxonomy', spec);
          } else if (tool.toolName === "visualizeRarefaction") {
            setPlotData('rarefaction', spec);
          } else if (tool.toolName === "visualizeStatistics") {
            setPlotData('statistics', spec);
          }
        }
      });
    }, 150);

    return () => clearTimeout(timeoutId);
  }, [JSON.stringify(mergedTools), isUser, setPlotData]);

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row",
        "w-full"
      )}
    >
      {(!isUser) && (
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent mt-0.5">
          <DnaIcon className="size-3.5 text-primary" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[85%] rounded-lg px-4 py-3 flex flex-col gap-2 shadow-sm border",
          isUser
            ? "bg-purple-600 border-purple-700 text-white"
            : "bg-white border-gray-200 text-gray-900 dark:bg-zinc-900 dark:border-zinc-800 dark:text-gray-100"
        )}
      >
        {textContent && (
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {textContent.split(/(\*\*.*?\*\*)/g).map((part: string, i: number) => {
              if (part.startsWith("**") && part.endsWith("**")) {
                return (
                  <strong key={i} className="font-semibold">
                    {part.slice(2, -2)}
                  </strong>
                )
              }
              return <span key={i}>{part}</span>
            })}
          </div>
        )}

        {mergedTools.length > 0 && (
          <div className="flex flex-col gap-3 mt-2 w-full">
            {mergedTools.map((toolPart: any, i: number) => {
              const isFinished = toolPart.state === "result" || !!toolPart.result
              let result = toolPart.result || toolPart.output

              // Unwrap React Server Component ({type, value}) serialization proxy
              if (result && typeof result === "object" && "type" in result && "value" in result && !result.plotly_spec) {
                let val = result.value;
                if (typeof val === "string") {
                  try { val = JSON.parse(val); } catch (e) {}
                }
                result = val;
              }

              const toolName = toolPart.toolName

              if (["visualizeAlphaDiversity", "visualizeBetaDiversity", "visualizeTaxonomy", "visualizeRarefaction", "visualizeStatistics"].includes(toolName)) {
                return (
                  <div key={i} className="rounded border border-border bg-background p-3 w-full shadow-sm max-w-[600px]">
                    <div className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-2">
                      <Microscope className="size-4 text-primary" />
                      {toolName === "visualizeAlphaDiversity"
                        ? "Alpha Diversity Analysis"
                        : toolName === "visualizeBetaDiversity"
                          ? "Beta Diversity Analysis"
                          : toolName === "visualizeTaxonomy"
                            ? "Taxonomic Composition"
                            : toolName === "visualizeRarefaction"
                              ? "Rarefaction Curve"
                              : "Statistics Analysis"
                      }
                    </div>
                    <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
                      {!isFinished ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-3">
                          <div className="size-6 animate-spin rounded-full border-b-2 border-primary" />
                          <span className="text-xs">Processando dados...</span>
                        </div>
                      ) : result?.error ? (
                        (() => {
                          const friendly = getFriendlyError(result.error);
                          return (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-destructive gap-2 p-4 text-center">
                              <span className="text-sm font-medium">{friendly.message}</span>
                              {friendly.hint && (
                                <span className="text-xs text-muted-foreground">{friendly.hint}</span>
                              )}
                            </div>
                          )
                        })()
                      ) : (
                        <Suspense fallback={<div className="flex w-full h-full items-center justify-center"><div className="size-6 rounded-full border-b-2 border-primary animate-spin" /></div>}>
                          {(result.plotly_spec?.data || result.data?.data) ? (
                            <div className="min-w-[500px] min-h-[400px] w-full h-full">
                              <PlotlyPlot data={result.plotly_spec?.data || result.data?.data} layout={result.plotly_spec?.layout || result.data?.layout} />
                            </div>
                          ) : (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-2 p-4 text-center">
                              <span className="text-sm font-medium">Nenhum dado gerado.</span>
                              <span className="text-xs">O arquivo carregado não produziu gráficos válidos para esta análise. Tente outra métrica.</span>
                            </div>
                          )}
                        </Suspense>
                      )}
                    </div>
                  </div>
                )
              }

              if (toolName === "parseData") {
                return (
                  <div key={i} className="text-xs italic text-muted-foreground bg-background/50 p-2 rounded w-fit">
                    {!isFinished ? "Parsing dataset..." : "Dataset loaded and parsed."}
                  </div>
                )
              }

              return null;
            })}
          </div>
        )}

        <p
          className={cn(
            "text-[10px]",
            isUser
              ? "text-primary-foreground/60 text-right mt-1"
              : "text-muted-foreground mt-1"
          )}
        >
          {message.timestamp ? message.timestamp : null}
        </p>
      </div>
    </div>
  )
}

import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"

export function ChatPanel({
  hasProject,
  projectId = "default",
  initialMessages = [],
  onOpenResults,
}: {
  hasProject: boolean
  projectId?: string
  initialMessages?: any[]
  onOpenResults?: () => void
}) {
  const { messages, setMessages, sendMessage, status } = useChat({
    id: projectId,
    // @ts-ignore
    initialMessages,
    transport: new DefaultChatTransport({
      api: "/api/chat",
      body: { projectId },
    }),
  });

  const prevProjectRef = useRef<string | null>(null);
  useEffect(() => {
    const isProjectChange = prevProjectRef.current !== projectId;
    prevProjectRef.current = projectId;
    // Force-reset messages when project changes OR when starting empty.
    // Needed because useChat caches state by id in memory — navigating away and
    // back would otherwise keep stale messages and ignore initialMessages from DB.
    if (isProjectChange || (initialMessages.length > 0 && messages.length === 0)) {
      setMessages(initialMessages);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, initialMessages]);

  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const isLoading = status === "streaming" || status === "submitted"

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + "px"
    }
  }, [input])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const onSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (input.trim()) {
      sendMessage({ text: input.trim() })
      setInput("")
    }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSubmit()
    }
  }

  if (!hasProject) {
    return (
      <div className="flex h-full flex-1 flex-col items-center justify-center gap-6 px-6">
        <div className="flex size-20 items-center justify-center rounded-2xl bg-accent">
          <Microscope className="size-10 text-primary" strokeWidth={1.5} />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground text-balance">
            Welcome to YARA
          </h1>
          <p className="mt-2 text-muted-foreground text-balance max-w-md">
            Upload a QIIME 2 file to start your metagenomic analysis
          </p>
        </div>
        <div className="w-full max-w-md">
          <FileUpload />
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 md:px-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center text-muted-foreground pt-20">
              Comece enviando uma mensagem ou fazendo upload de mais arquivos.
            </div>
          )}
          {(() => {
            let lastUserText = "";
            return messages.map((message: any) => {
              if (message.role === "user") {
                lastUserText = getTextFromMessage(message);
                return <MessageBubble key={message.id} message={message} />;
              }

              return (
                <MessageBubble
                  key={message.id}
                  message={message}
                  allowedToolNames={getRequestedToolNames(lastUserText)}
                />
              );
            });
          })()}

          {isLoading && (
            <div className="text-sm text-muted-foreground mt-2 flex items-center gap-2">
              <div className="size-4 animate-spin rounded-full border-b-2 border-primary"></div>
              YARA is analyzing...
            </div>
          )}
          {/* Sentinel for auto-scroll */}
          <div ref={bottomRef} />
        </div>
      </div>

      <form onSubmit={onSubmit} className="border-t border-border bg-background px-4 pb-4 pt-3 md:px-6">
        <div className="mx-auto max-w-2xl">
          <div className="mb-3 flex flex-wrap gap-2">
            {suggestionChips.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => {
                  sendMessage({ text: chip })
                  setInput("")
                }}
                className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
              >
                {chip}
              </button>
            ))}
          </div>

          <div className="flex items-end gap-2 rounded-lg border border-border bg-background p-2 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-ring/30 transition-[border-color,box-shadow]">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="shrink-0 text-muted-foreground hover:text-foreground"
              aria-label="Attach file"
            >
              <Paperclip className="size-4" />
            </Button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask YARA about your data..."
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none min-h-[36px] max-h-[120px] py-1.5"
            />
            <Button
              type="submit"
              size="icon-sm"
              className={cn(
                "shrink-0 transition-opacity",
                input.trim()
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-muted text-muted-foreground pointer-events-none opacity-50"
              )}
              disabled={!input.trim() || isLoading}
              aria-label="Send message"
            >
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}
