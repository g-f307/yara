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
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useResultsStore } from "@/store/use-results-store"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu, BarChart2 } from "lucide-react"
import { YaraLogo } from "@/components/yara-logo"

interface ProjectLayoutClientProps {
    projectId: string;
    projects: SidebarProject[];
    initialMessages?: any[];
    projectFiles?: any[];
    projectSessions?: any[];
}

export default function ProjectLayoutClient({ projectId, projects, initialMessages, projectFiles, projectSessions }: ProjectLayoutClientProps) {
    const router = useRouter();
    const resetStore = useResultsStore((state: any) => state.reset);
    const currentProject = projects.find(p => p.id === projectId);
    const [hasData, setHasData] = useState(() => {
        if (currentProject && currentProject.fileCount > 0) return true;
        return false;
    });
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [resultsOpen, setResultsOpen] = useState(false);

    useEffect(() => {
        resetStore();
    }, [projectId, resetStore]);

    // Inform the Dialog portal that a sidebar is present so it can center correctly (desktop only)
    useEffect(() => {
        const updateClass = () => {
            if (window.innerWidth >= 1024) {
                document.body.classList.add('has-sidebar');
            } else {
                document.body.classList.remove('has-sidebar');
            }
        };
        updateClass();
        window.addEventListener('resize', updateClass);
        return () => {
            document.body.classList.remove('has-sidebar');
            window.removeEventListener('resize', updateClass);
        };
    }, []);

    return (
        <div className="fixed inset-0 flex bg-background text-foreground overflow-hidden">
            {/* Desktop Sidebar (visible on 1024px and up) */}
            <div className="desktop-only h-full">
                <ProjectSidebar
                    projects={projects}
                    activeProjectId={projectId}
                    onSelectProject={(id) => router.push(`/project/${id}`)}
                />
            </div>

            {/* Mobile: top header bar (visible on < 1024px) */}
            <div className="mobile-only absolute top-0 left-0 right-0 z-20 items-center justify-between border-b border-border bg-background/95 backdrop-blur px-3 py-2">
                {/* Hamburger → sidebar drawer */}
                <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
                    <SheetTrigger asChild>
                        <Button variant="ghost" size="icon-sm">
                            <Menu className="size-5" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="p-0 w-[260px]">
                        <SheetTitle className="sr-only">Navegação de projetos</SheetTitle>
                        <ProjectSidebar
                            projects={projects}
                            activeProjectId={projectId}
                            onSelectProject={(id) => { setSidebarOpen(false); router.push(`/project/${id}`); }}
                        />
                    </SheetContent>
                </Sheet>

                <YaraLogo />

                {/* Results panel toggle (mobile) */}
                {hasData ? (
                    <Sheet open={resultsOpen} onOpenChange={setResultsOpen}>
                        <SheetTrigger asChild>
                            <Button variant="ghost" size="icon-sm">
                                <BarChart2 className="size-5" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="right" className="p-0 w-full sm:w-[480px]">
                            <SheetTitle className="sr-only">Painel de Resultados</SheetTitle>
                            <ResultsPanel projectId={projectId} files={projectFiles} sessions={projectSessions} />
                        </SheetContent>
                    </Sheet>
                ) : (
                    <div className="w-8" /> // placeholder for spacing
                )}
            </div>

            {/* Main workspace */}
            <main className="flex-1 flex flex-col min-w-0 min-h-0 relative">
                {/* Mobile top spacing */}
                <div className="mobile-only-block h-[46px] shrink-0" />

                <div className="flex-1 flex flex-col overflow-hidden">
                    {hasData ? (
                        <>
                            {/* Desktop: resizable panels */}
                            <div className="desktop-only flex-1 h-full w-full">
                                <ResizablePanelGroup direction="horizontal">
                                    <ResizablePanel defaultSize={45} minSize={30}>
                                        <ChatPanel
                                            key={projectId}
                                            projectId={projectId}
                                            hasProject={true}
                                            initialMessages={initialMessages}
                                        />
                                    </ResizablePanel>
                                    <ResizableHandle className="w-1.5 hover:bg-primary/20 transition-colors" />
                                    <ResizablePanel defaultSize={55} minSize={40}>
                                        <ResultsPanel projectId={projectId} files={projectFiles} sessions={projectSessions} />
                                    </ResizablePanel>
                                </ResizablePanelGroup>
                            </div>

                            {/* Mobile: only chat */}
                            <div className="mobile-only flex-1 relative flex-col h-full w-full">
                                <ChatPanel
                                    key={projectId}
                                    projectId={projectId}
                                    hasProject={true}
                                    initialMessages={initialMessages}
                                />
                            </div>
                        </>
                    ) : (
                        <div className="flex h-full flex-col p-4 md:p-6 overflow-y-auto">
                            <div className="flex-1 rounded-xl border border-border bg-card shadow-sm p-6 md:p-8 flex flex-col items-center justify-center relative overflow-hidden min-h-[400px]">
                                <div className="absolute inset-0 bg-grid-black/[0.02] dark:bg-grid-white/[0.02]" />
                                <div className="relative z-10 w-full max-w-2xl mx-auto space-y-8">
                                    <div className="text-center space-y-2">
                                        <h2 className="text-xl md:text-2xl font-semibold tracking-tight">Upload sua base de dados</h2>
                                        <p className="text-muted-foreground text-sm">
                                            Envie arquivos <code className="px-1.5 py-0.5 rounded bg-muted text-foreground">.qzv</code> ou
                                            <code className="px-1.5 py-0.5 rounded bg-muted text-foreground ml-1">.tsv</code> exportados do QIIME 2 para iniciar a análise.
                                        </p>
                                    </div>
                                    <div className="bg-background rounded-xl p-4 md:p-6 border shadow-sm flex flex-col items-center gap-4">
                                        <div className="w-full">
                                            <FileUpload projectId={projectId} onFileSelect={() => setHasData(true)} />
                                        </div>
                                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                                            <span>ou apenas</span>
                                            <button
                                                onClick={() => setHasData(true)}
                                                className="text-primary hover:underline font-medium"
                                            >
                                                testar com dados de demonstração
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
