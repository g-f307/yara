"use client"

import { useState, useCallback } from "react"
import { Upload, FileText, X, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"

const ACCEPTED_TYPES = [".tsv", ".qzv", ".qza", ".biom"]

interface FileUploadProps {
  compact?: boolean
  onFileSelect?: (file: File) => void
}

export function FileUpload({ compact = false, onFileSelect }: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<{
    name: string
    size: string
    type: string
  } | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const getFileExtension = (name: string) => {
    const ext = "." + name.split(".").pop()?.toLowerCase()
    return ext
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
    return (bytes / (1024 * 1024)).toFixed(1) + " MB"
  }

  const handleFile = useCallback(
    (file: File) => {
      setError(null)
      const ext = getFileExtension(file.name)
      if (!ACCEPTED_TYPES.includes(ext)) {
        setError(
          `Unsupported format "${ext}". Accepted: ${ACCEPTED_TYPES.join(", ")}`
        )
        return
      }
      setSelectedFile({
        name: file.name,
        size: formatSize(file.size),
        type: ext,
      })
      setUploading(true)
      setProgress(0)

      // Simulate upload
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            setUploading(false)
            return 100
          }
          return prev + 20
        })
      }, 300)

      onFileSelect?.(file)
    },
    [onFileSelect]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file) handleFile(file)
    },
    [handleFile]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false)
  }, [])

  const clearFile = () => {
    setSelectedFile(null)
    setProgress(0)
    setUploading(false)
    setError(null)
  }

  if (selectedFile) {
    return (
      <div className="rounded-lg border border-border bg-card p-3">
        <div className="flex items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent">
            <FileText className="size-4 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-card-foreground">
              {selectedFile.name}
            </p>
            <p className="text-xs text-muted-foreground">
              {selectedFile.size}
            </p>
          </div>
          <button
            onClick={clearFile}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Remove file"
          >
            <X className="size-4" />
          </button>
        </div>
        {uploading && (
          <div className="mt-2">
            <Progress value={progress} className="h-1.5 [&>div]:bg-primary" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          "relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors",
          compact ? "gap-2 p-6" : "gap-3 p-10",
          isDragOver
            ? "border-primary bg-accent"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/50",
          error && "border-destructive"
        )}
        role="button"
        tabIndex={0}
        aria-label="Upload file by dragging and dropping or clicking"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            document.getElementById("file-input")?.click()
          }
        }}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          className="sr-only"
          accept={ACCEPTED_TYPES.join(",")}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />
        <div className="flex size-10 items-center justify-center rounded-full bg-accent">
          <Upload className="size-5 text-primary" />
        </div>
        <div className="text-center">
          <p className={cn("font-medium text-foreground", compact ? "text-sm" : "text-base")}>
            Drop your file here or{" "}
            <span className="text-primary">browse</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Supports .tsv, .qzv, .qza, .biom
          </p>
        </div>
      </div>
      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive-foreground">
          <AlertCircle className="size-4 shrink-0" />
          {error}
        </div>
      )}
    </div>
  )
}
