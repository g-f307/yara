import { createHmac, timingSafeEqual } from "crypto";
import { headers } from "next/headers";
import type { NextRequest } from "next/server";
import { prisma } from "@/lib/db";
import { logRequest, publicErrorResponse, REQUEST_ID_HEADER, requestId } from "@/lib/observability";

export const runtime = "nodejs";

type ClerkEmailAddress = {
  email_address?: string;
};

type ClerkUserPayload = {
  id: string;
  email_addresses?: ClerkEmailAddress[];
  first_name?: string | null;
  last_name?: string | null;
};

type ClerkWebhookEvent = {
  type: string;
  data: ClerkUserPayload;
};

function decodeSvixSecret(secret: string) {
  return Buffer.from(secret.replace(/^whsec_/, ""), "base64");
}

function verifySvixSignature(body: string, secret: string, id: string, timestamp: string, signature: string) {
  const payload = `${id}.${timestamp}.${body}`;
  const digest = createHmac("sha256", decodeSvixSecret(secret)).update(payload).digest("base64");

  return signature
    .split(" ")
    .some((candidate) => {
      const [, value] = candidate.split(",");
      if (!value) return false;

      const expected = Buffer.from(digest);
      const received = Buffer.from(value);
      return expected.length === received.length && timingSafeEqual(expected, received);
    });
}

export async function POST(req: NextRequest) {
  const started = performance.now();
  const correlationId = requestId(req.headers.get(REQUEST_ID_HEADER));
  const fail = (code: string, message: string, status: number) => {
    logRequest({ requestId: correlationId, method: "POST", path: "/api/webhooks/clerk", status, durationMs: performance.now() - started, errorCode: code });
    return publicErrorResponse(code, message, correlationId, status);
  };
  const webhookSecret = process.env.CLERK_WEBHOOK_SECRET;
  if (!webhookSecret) {
    return fail("INTERNAL_ERROR", "O webhook não está configurado.", 500);
  }

  const headerPayload = await headers();
  const svixId = headerPayload.get("svix-id");
  const svixTimestamp = headerPayload.get("svix-timestamp");
  const svixSignature = headerPayload.get("svix-signature");

  if (!svixId || !svixTimestamp || !svixSignature) {
    return fail("INVALID_REQUEST", "Requisição inválida.", 400);
  }

  const body = await req.text();
  if (!verifySvixSignature(body, webhookSecret, svixId, svixTimestamp, svixSignature)) {
    return fail("INVALID_REQUEST", "Requisição inválida.", 400);
  }

  try {
    const event = JSON.parse(body) as ClerkWebhookEvent;
    if (event.type === "user.created" || event.type === "user.updated") {
      const { id, email_addresses, first_name, last_name } = event.data;
      const email = email_addresses?.[0]?.email_address;

      if (!email) {
        return fail("INVALID_REQUEST", "Requisição inválida.", 400);
      }

      const name = [first_name, last_name].filter(Boolean).join(" ") || "Usuario YARA";

      await prisma.user.upsert({
        where: { clerkId: id },
        update: { email, name },
        create: { clerkId: id, email, name },
      });
    }
  } catch {
    return fail("INTERNAL_ERROR", "Não foi possível processar o webhook.", 500);
  }

  logRequest({ requestId: correlationId, method: "POST", path: "/api/webhooks/clerk", status: 200, durationMs: performance.now() - started });
  return new Response("OK", { status: 200, headers: { "X-Request-ID": correlationId } });
}
