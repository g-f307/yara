import { createRouteHandler } from "uploadthing/next";
import { NextRequest } from "next/server";
import { ourFileRouter } from "./core";

export const { GET, POST } = createRouteHandler({
    router: ourFileRouter,
});

export const dynamic = "force-dynamic";
