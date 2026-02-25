"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Paperclip, Microscope } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
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

function MessageBubble({ message }: { message: any }) {
  const isUser = message.role === "user"

  // Check if there are tool invocations
  const hasTools = message.toolInvocations && message.toolInvocations.length > 0;

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row",
        "w-full"
      )}
    >
      {!isUser && (
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent mt-0.5">
          <DnaIcon className="size-3.5 text-primary" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[85%] rounded-lg px-4 py-3 flex flex-col gap-2",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        )}
      >
        {message.content && (
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content.split(/(\*\*.*?\*\*)/g).map((part: string, i: number) => {
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

        {hasTools && (
          <div className="flex flex-col gap-3 mt-2 w-full">
            {message.toolInvocations.map((toolReq: any, i: number) => {
              // Extract the result if completed
              const result = toolReq.result;
              const isFinished = toolReq.state === "result";

              if (toolReq.toolName === "visualizeAlphaDiversity" || toolReq.toolName === "visualizeBetaDiversity" || toolReq.toolName === "visualizeTaxonomy" || toolReq.toolName === "visualizeRarefaction") {
                return (
                  <div key={i} className="rounded border border-border bg-background p-3 w-full shadow-sm max-w-[600px]">
                    <div className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-2">
                      <Microscope className="size-4 text-primary" />
                      {toolReq.toolName === "visualizeAlphaDiversity"
                        ? "Alpha Diversity Analysis"
                        : toolReq.toolName === "visualizeBetaDiversity"
                          ? "Beta Diversity Analysis"
                          : toolReq.toolName === "visualizeTaxonomy"
                            ? "Taxonomic Composition"
                            : "Rarefaction Curve"
                      }
                    </div>
                    <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
                      {!isFinished || !result?.data ? (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="size-6 animate-spin rounded-full border-b-2 border-primary" />
                        </div>
                      ) : (
                        <Suspense fallback={<div className="flex w-full h-full items-center justify-center"><div className="size-6 rounded-full border-b-2 border-primary animate-spin" /></div>}>
                          <div className="min-w-[500px] min-h-[400px] w-full h-full">
                            <PlotlyPlot data={result.data.data} layout={result.data.layout} />
                          </div>
                        </Suspense>
                      )}
                    </div>
                  </div>
                )
              }

              if (toolReq.toolName === "parseData") {
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
          {message.timestamp || new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
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
  onOpenResults,
}: {
  hasProject: boolean
  projectId?: string
  onOpenResults?: () => void
}) {
  const { messages, sendMessage, status } = useChat({
    id: projectId,
    transport: new DefaultChatTransport({
      api: "/api/chat",
      body: { projectId },
    }),
  });

  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isLoading = status === "streaming" || status === "submitted"

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + "px"
    }
  }, [input])

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
    <div className="flex h-full flex-1 flex-col">
      <ScrollArea className="flex-1 px-4 py-4 md:px-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-4">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-muted-foreground pt-20">
              Comece enviando uma mensagem ou fazendo upload de mais arquivos.
            </div>
          )}
          {messages.map((message: any) => (
            <MessageBubble key={message.id} message={{
              ...message,
              timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
            }} />
          ))}
          {isLoading && (
            <div className="text-sm text-muted-foreground mt-2 flex items-center gap-2">
              <div className="size-4 animate-spin rounded-full border-b-2 border-primary"></div>
              YARA is analyzing...
            </div>
          )}
        </div>
      </ScrollArea>

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
