"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { renameProject } from "@/lib/actions"
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

interface RenameProjectDialogProps {
    projectId: string
    currentName: string
    children: React.ReactNode
    onRename?: (newName: string) => void
}

export function RenameProjectDialog({ projectId, currentName, children, onRename }: RenameProjectDialogProps) {
    const [open, setOpen] = useState(false)
    const [name, setName] = useState(currentName)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()

    const handleOpenChange = (newOpen: boolean) => {
        setOpen(newOpen)
        if (newOpen) setName(currentName)
        setError(null)
    }

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        const trimmed = name.trim()
        if (!trimmed || trimmed === currentName) {
            setOpen(false)
            return
        }

        setIsLoading(true)
        setError(null)
        const result = await renameProject(projectId, trimmed)
        setIsLoading(false)

        if (result.success) {
            setOpen(false)
            onRename?.(trimmed)
            router.refresh()
        } else {
            setError(result.error || "Erro ao renomear projeto")
        }
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogTrigger asChild>{children}</DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={onSubmit}>
                    <DialogHeader>
                        <DialogTitle>Renomear projeto</DialogTitle>
                        <DialogDescription>
                            Altere o nome do projeto. Esta ação não afeta os dados ou análises existentes.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="flex flex-col gap-3">
                            <Label htmlFor="rename-project">Nome do projeto</Label>
                            <Input
                                id="rename-project"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g. Amazon Soil Microbiome"
                                autoFocus
                            />
                            {error && (
                                <p className="text-xs text-destructive">{error}</p>
                            )}
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            Cancelar
                        </Button>
                        <Button type="submit" disabled={!name.trim() || isLoading}>
                            {isLoading ? "Salvando..." : "Salvar"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
