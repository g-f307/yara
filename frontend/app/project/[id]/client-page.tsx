"use client"

import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from "@/components/ui/resizable"
import { ProjectSidebar, type SidebarProject } from "@/components/project-sidebar"
import { ResultsPanel } from "@/components/results-panel"
import { ChatPanel } from "@/components/chat-panel"
import { FileUpload } from "@/components/file-upload"
import { useState } from "react"
import { UploadDropzone } from "@/lib/uploadthing"
import { useRouter } from "next/navigation"

interface ProjectLayoutClientProps {
    projectId: string;
    projects: SidebarProject[];
}

export default function ProjectLayoutClient({ projectId, projects }: ProjectLayoutClientProps) {
    const router = useRouter();
    const currentProject = projects.find(p => p.id === projectId);
    const [hasData, setHasData] = useState(() => {
        if (currentProject && currentProject.fileCount > 0) return true;
        return false;
    });

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            {/* Sidebar with projects list */}
            <ProjectSidebar
                projects={projects}
                activeProjectId={projectId}
                onSelectProject={(id) => router.push(`/project/${id}`)}
            />

            {/* Main workspace */}
            <main className="flex-1 flex flex-col min-w-0">
                <div className="flex-1 overflow-hidden">
                    {hasData ? (
                        <ResizablePanelGroup direction="horizontal">
                            {/* Chat Panel */}
                            <ResizablePanel defaultSize={45} minSize={30}>
                                <ChatPanel projectId={projectId} hasProject={true} />
                            </ResizablePanel>

                            <ResizableHandle className="w-1.5 hover:bg-primary/20 transition-colors" />

                            {/* Analysis/Results Panel */}
                            <ResizablePanel defaultSize={55} minSize={40}>
                                <ResultsPanel projectId={projectId} />
                            </ResizablePanel>
                        </ResizablePanelGroup>
                    ) : (
                        <div className="flex h-full flex-col p-6">
                            <div className="flex-1 rounded-xl border border-border bg-card shadow-sm p-8 flex flex-col items-center justify-center relative overflow-hidden">
                                <div className="absolute inset-0 bg-grid-black/[0.02] dark:bg-grid-white/[0.02]" />

                                <div className="relative z-10 w-full max-w-2xl mx-auto space-y-8">
                                    <div className="text-center space-y-2">
                                        <h2 className="text-2xl font-semibold tracking-tight">Upload sua base de dados</h2>
                                        <p className="text-muted-foreground text-sm">
                                            Envie arquivos <code className="px-1.5 py-0.5 rounded bg-muted text-foreground">.qzv</code> ou
                                            <code className="px-1.5 py-0.5 rounded bg-muted text-foreground ml-1">.tsv</code> exportados do QIIME 2 para iniciar a análise.
                                        </p>
                                    </div>

                                    <div className="bg-background rounded-xl p-6 border shadow-sm flex flex-col items-center gap-4">
                                        <div className="w-full">
                                            <FileUpload projectId={projectId} onFileSelect={() => setHasData(true)} />
                                        </div>
                                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                                            <span>ou apenas</span>
                                            <button
                                                onClick={() => setHasData(true)}
                                                className="text-primary hover:underline font-medium"
                                            >
                                                testar o chat com dados falsos
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    )
}
