import crypto from "node:crypto";
if (typeof globalThis.crypto === "undefined") {
    // @ts-ignore
    globalThis.crypto = crypto;
}

import { createUploadthing, type FileRouter } from "uploadthing/next";
import { UploadThingError } from "uploadthing/server";
import { auth } from "@clerk/nextjs/server";

const f = createUploadthing();

// FileRouter for your app, can contain multiple FileRoutes
export const ourFileRouter = {
    // Define as many FileRoutes as you like, each with a unique routeSlug
    dataUploader: f({
        blob: { maxFileSize: "128MB", maxFileCount: 10 },
    })
        // Set permissions and file types for this FileRoute
        .middleware(async () => {
            // This code runs on your server before upload
            // Here we check auth via Clerk
            const { userId } = await auth();
            if (!userId) throw new UploadThingError("Unauthorized");
            return { userId };
        })
        .onUploadComplete(async ({ metadata }) => {
            // This code RUNS ON YOUR SERVER after upload
            // We will save to Prisma DB in the UI or here later
            return { uploadedBy: metadata.userId };
        }),
} satisfies FileRouter;

export type OurFileRouter = typeof ourFileRouter;
