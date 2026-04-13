import { createHmac, timingSafeEqual } from "crypto";
import { headers } from "next/headers";
import type { NextRequest } from "next/server";
import { prisma } from "@/lib/db";

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
  const webhookSecret = process.env.CLERK_WEBHOOK_SECRET;
  if (!webhookSecret) {
    return new Response("CLERK_WEBHOOK_SECRET is not configured", { status: 500 });
  }

  const headerPayload = await headers();
  const svixId = headerPayload.get("svix-id");
  const svixTimestamp = headerPayload.get("svix-timestamp");
  const svixSignature = headerPayload.get("svix-signature");

  if (!svixId || !svixTimestamp || !svixSignature) {
    return new Response("Missing Svix headers", { status: 400 });
  }

  const body = await req.text();
  if (!verifySvixSignature(body, webhookSecret, svixId, svixTimestamp, svixSignature)) {
    return new Response("Invalid signature", { status: 400 });
  }

  const event = JSON.parse(body) as ClerkWebhookEvent;
  if (event.type === "user.created" || event.type === "user.updated") {
    const { id, email_addresses, first_name, last_name } = event.data;
    const email = email_addresses?.[0]?.email_address;

    if (!email) {
      return new Response("User email not found", { status: 400 });
    }

    const name = [first_name, last_name].filter(Boolean).join(" ") || "Usuario YARA";

    await prisma.user.upsert({
      where: { clerkId: id },
      update: { email, name },
      create: { clerkId: id, email, name },
    });
  }

  return new Response("OK", { status: 200 });
}
