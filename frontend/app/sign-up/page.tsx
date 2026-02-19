import Link from "next/link"
import { DnaIcon } from "@/components/yara-logo"
import { Button } from "@/components/ui/button"

export default function SignUpPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <DnaIcon className="size-6" />
          </div>
          <h1 className="text-xl font-semibold text-foreground">
            Create your account
          </h1>
          <p className="text-sm text-muted-foreground text-center text-balance">
            Start analyzing metagenomic data with YARA
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="name" className="text-sm font-medium text-card-foreground">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                placeholder="Dr. Jane Smith"
                className="h-9 rounded-lg border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-sm font-medium text-card-foreground">
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="researcher@lab.edu"
                className="h-9 rounded-lg border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-sm font-medium text-card-foreground">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Create a password"
                className="h-9 rounded-lg border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>
            <Link href="/dashboard">
              <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                Create Account
              </Button>
            </Link>
          </div>
        </div>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link
            href="/sign-in"
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </main>
  )
}
