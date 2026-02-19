"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { ProjectSidebar } from "@/components/project-sidebar"
import { ChatPanel } from "@/components/chat-panel"
import { ResultsPanel } from "@/components/results-panel"
import { MobileTopBar, MobileTabBar } from "@/components/mobile-nav"
import { ResultsPanel as ResultsPanelContent } from "@/components/results-panel"
import { cn } from "@/lib/utils"

export default function ProjectPage() {
  const params = useParams()
  const projectId = params.id as string
  const [activeProjectId, setActiveProjectId] = useState<string>(projectId)
  const [mobileTab, setMobileTab] = useState<"chat" | "files" | "results">("chat")
  const [showResults, setShowResults] = useState(true)

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Mobile top bar */}
      <MobileTopBar
        activeProjectId={activeProjectId}
        onSelectProject={setActiveProjectId}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar — hidden on mobile, icon rail on tablet, full on desktop */}
        <div className="hidden lg:block">
          <ProjectSidebar
            activeProjectId={activeProjectId}
            onSelectProject={setActiveProjectId}
          />
        </div>
        <div className="hidden md:block lg:hidden">
          <ProjectSidebar
            activeProjectId={activeProjectId}
            onSelectProject={setActiveProjectId}
            collapsed
          />
        </div>

        {/* Chat panel — visible on all breakpoints when chat tab is active */}
        <div
          className={cn(
            "flex-1 overflow-hidden",
            mobileTab !== "chat" && "hidden md:flex"
          )}
        >
          <ChatPanel
            hasProject={true}
            onOpenResults={() => setShowResults(true)}
          />
        </div>

        {/* Right results panel — hidden on mobile unless results tab, sheet on tablet, full on desktop */}
        <div
          className={cn(
            "w-full md:w-[320px] shrink-0 overflow-hidden",
            mobileTab === "results" ? "block md:block" : "hidden md:hidden lg:block"
          )}
        >
          <ResultsPanel className="h-full" />
        </div>

        {/* Files tab on mobile — reuses results panel files tab */}
        {mobileTab === "files" && (
          <div className="flex-1 md:hidden">
            <ResultsPanel className="h-full border-l-0" />
          </div>
        )}
      </div>

      {/* Mobile bottom tab bar */}
      <MobileTabBar activeTab={mobileTab} onTabChange={setMobileTab} />
    </div>
  )
}
