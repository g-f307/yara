import crypto from "node:crypto";
if (typeof globalThis.crypto === "undefined") {
    // @ts-ignore
    globalThis.crypto = crypto;
}

import { createUploadthing, type FileRouter } from "uploadthing/next";
import { UploadThingError } from "uploadthing/server";

const f = createUploadthing();

// FileRouter for your app, can contain multiple FileRoutes
export const ourFileRouter = {
    // Define as many FileRoutes as you like, each with a unique routeSlug
    dataUploader: f({
        blob: { maxFileSize: "128MB", maxFileCount: 10 },
    })
        // Set permissions and file types for this FileRoute
        .middleware(async ({ req }) => {
            console.log("UPLOADTHING MIDDLEWARE CALLED");
            // This code runs on your server before upload
            // Here we would typically check auth via Clerk
            // const user = await auth();
            // if (!user) throw new UploadThingError("Unauthorized");
            return { userId: "temp-user-id" };
        })
        .onUploadComplete(async ({ metadata, file }) => {
            // This code RUNS ON YOUR SERVER after upload
            console.log("UPLOADTHING COMPLETE CALLED for userId:", metadata.userId);
            console.log("file url", file.url);

            // We will save to Prisma DB in the UI or here later
            return { uploadedBy: metadata.userId || "temp-user" };
        }),
} satisfies FileRouter;

export type OurFileRouter = typeof ourFileRouter;
