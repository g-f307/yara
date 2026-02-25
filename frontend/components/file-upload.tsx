"use client"

import { cn } from "@/lib/utils"

interface FileUploadProps {
  compact?: boolean
  projectId?: string
  onFileSelect?: (file: File) => void
}

import { UploadDropzone } from "@/lib/uploadthing";

export function FileUpload({ compact = false, projectId, onFileSelect }: FileUploadProps) {
  return (
    <div className={cn("w-full", compact && "p-2")}>
      <UploadDropzone
        endpoint="dataUploader"
        onClientUploadComplete={(res) => {
          // Do something with the response
          console.log("Files: ", res);
          alert("Upload Completed");
          if (onFileSelect && res.length > 0) {
            // Hacky translation of Uploadthing file to local state requirement
            // We'd actually want to pass the URL/key and update DB
            onFileSelect(new File([], res[0].name));
          }
        }}
        onUploadError={(error: Error) => {
          alert(`ERROR! ${error.message}`);
        }}
        className="ut-button:bg-primary ut-button:text-primary-foreground ut-label:text-primary ut-allowed-content:text-muted-foreground border-border hover:border-primary/50 transition-colors bg-accent/20"
      />
    </div>
  )
}
