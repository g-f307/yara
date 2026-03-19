"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createProject } from "@/lib/actions"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function CreateProjectDialog({ children }: { children: React.ReactNode }) {
    const [open, setOpen] = useState(false)
    const [name, setName] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const router = useRouter()

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!name.trim()) return

        setIsLoading(true)
        const result = await createProject(name)
        setIsLoading(false)

        if (result.success && result.project) {
            setOpen(false)
            router.push(`/project/${result.project.id}`)
        } else {
            console.error(result.error)
        }
    }

    // Clear name when dialog closes
    const handleOpenChange = (newOpen: boolean) => {
        setOpen(newOpen)
        if (!newOpen) setName("")
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogTrigger asChild>
                {children}
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={onSubmit}>
                    <DialogHeader>
                        <DialogTitle>Criar novo projeto</DialogTitle>
                        <DialogDescription>
                            Dê um nome para o seu projeto de análise metagenômica para começar.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="flex flex-col gap-3">
                            <Label htmlFor="name">
                                Nome do projeto
                            </Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="ex.: Microbioma do Solo Amazônico"
                                autoFocus
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            Cancelar
                        </Button>
                        <Button type="submit" disabled={!name.trim() || isLoading}>
                            {isLoading ? "Criando..." : "Criar Projeto"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
