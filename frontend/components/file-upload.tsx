"use client"

import { cn } from "@/lib/utils"

interface FileUploadProps {
  compact?: boolean
  projectId?: string
  onFileSelect?: (file: File, validation?: any) => void
}

import { UploadDropzone } from "@/lib/uploadthing";
import { createProjectFile, validateProjectData } from "@/lib/actions";
import { toast } from "sonner";

export function FileUpload({ compact = false, projectId, onFileSelect }: FileUploadProps) {
  return (
    <div className={cn("w-full", compact && "p-2")}>
      <UploadDropzone
        endpoint="dataUploader"
        onClientUploadComplete={async (res) => {
          console.log("Files uploaded to UploadThing:", res);

          if (res && res.length > 0) {
            try {
              if (projectId) {
                // Save all uploaded files to the database
                for (const file of res) {
                  const fileExtension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
                  const result = await createProjectFile(projectId, {
                    name: file.name,
                    type: fileExtension,
                    url: file.url,
                    key: file.key,
                    size: file.size,
                  });
                  if (result?.error) {
                    console.error("Server action error:", result.error);
                    alert(`Falha ao salvar no banco: ${result.error}`);
                  }
                }

                const validation = await validateProjectData(projectId);
                if (validation.success) {
                  const detected = validation.data?.detected_types ?? [];
                  const warnings = validation.data?.warnings ?? [];
                  if (detected.length > 0) {
                    toast.success(`Dados prontos para: ${detected.join(", ")}`);
                  } else if (warnings.length > 0) {
                    toast.warning(warnings[0]);
                  } else {
                    toast.info("Upload concluido. Peça uma análise ao YARA para continuar.");
                  }
                } else {
                  toast.error(validation.error || "Não foi possível validar os arquivos enviados.");
                }

                if (onFileSelect) {
                  onFileSelect(new File([], res[0].name), validation.success ? validation.data : undefined);
                  return;
                }
              }
              if (onFileSelect) {
                onFileSelect(new File([], res[0].name));
              }
            } catch (err: any) {
              console.error("Error during upload completion:", err);
              alert(`Erro interno do Next.js: ${err.message || String(err)}`);
            }
          }
        }}
        onUploadError={(error: Error) => {
          alert(`Errror: ${error.message}`);
        }}
        config={{ mode: "auto", appendOnPaste: true }}
        className="ut-button:bg-primary ut-button:text-primary-foreground ut-label:text-primary ut-allowed-content:text-muted-foreground border-border hover:border-primary/50 transition-colors bg-accent/20"
      />
    </div>
  )
}
