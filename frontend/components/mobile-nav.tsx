"use client"

import { MessageSquare, FolderOpen, BarChart3, Menu } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet"
import { ProjectSidebar } from "@/components/project-sidebar"

type MobileTab = "chat" | "files" | "results"

const tabs: { id: MobileTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "files", label: "Files", icon: FolderOpen },
  { id: "results", label: "Results", icon: BarChart3 },
]

export function MobileTopBar({
  activeProjectId,
  onSelectProject,
}: {
  activeProjectId: string | null
  onSelectProject: (id: string) => void
}) {
  return (
    <header className="flex items-center gap-2 border-b border-border bg-background px-3 py-2.5 md:hidden">
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label="Open navigation">
            <Menu className="size-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-[280px] p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <ProjectSidebar
            activeProjectId={activeProjectId}
            onSelectProject={onSelectProject}
          />
        </SheetContent>
      </Sheet>
      <span className="text-sm font-semibold text-foreground">YARA</span>
    </header>
  )
}

export function MobileTabBar({
  activeTab,
  onTabChange,
}: {
  activeTab: MobileTab
  onTabChange: (tab: MobileTab) => void
}) {
  return (
    <nav className="flex items-center border-t border-border bg-background md:hidden" aria-label="Main navigation">
      {tabs.map((tab) => {
        const Icon = tab.icon
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium transition-colors",
              activeTab === tab.id
                ? "text-primary"
                : "text-muted-foreground"
            )}
            aria-current={activeTab === tab.id ? "page" : undefined}
          >
            <Icon className="size-5" />
            {tab.label}
          </button>
        )
      })}
    </nav>
  )
}
