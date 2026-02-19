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

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {!isUser && (
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent mt-0.5">
          <DnaIcon className="size-3.5 text-primary" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2.5",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        )}
      >
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content.split(/(\*\*.*?\*\*)/g).map((part, i) => {
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
        {message.analysisCard && (
          <AnalysisCard data={message.analysisCard} />
        )}
        <p
          className={cn(
            "mt-1.5 text-[10px]",
            isUser
              ? "text-primary-foreground/60 text-right"
              : "text-muted-foreground"
          )}
        >
          {message.timestamp}
        </p>
      </div>
    </div>
  )
}

export function ChatPanel({
  hasProject,
  onOpenResults,
}: {
  hasProject: boolean
  onOpenResults?: () => void
}) {
  const [inputValue, setInputValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + "px"
    }
  }, [inputValue])

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
          {mockMessages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-background px-4 pb-4 pt-3 md:px-6">
        <div className="mx-auto max-w-2xl">
          <div className="mb-3 flex flex-wrap gap-2">
            {suggestionChips.map((chip) => (
              <button
                key={chip}
                onClick={() => setInputValue(chip)}
                className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
              >
                {chip}
              </button>
            ))}
          </div>

          <div className="flex items-end gap-2 rounded-lg border border-border bg-background p-2 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-ring/30 transition-[border-color,box-shadow]">
            <Button
              variant="ghost"
              size="icon-sm"
              className="shrink-0 text-muted-foreground hover:text-foreground"
              aria-label="Attach file"
            >
              <Paperclip className="size-4" />
            </Button>
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask YARA about your data..."
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none min-h-[36px] max-h-[120px] py-1.5"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                }
              }}
            />
            <Button
              size="icon-sm"
              className={cn(
                "shrink-0 transition-opacity",
                inputValue.trim()
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-muted text-muted-foreground pointer-events-none opacity-50"
              )}
              disabled={!inputValue.trim()}
              aria-label="Send message"
            >
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
