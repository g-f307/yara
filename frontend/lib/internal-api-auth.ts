import "server-only";

import internalApiAuthCore from "./internal-api-auth-core.cjs";

const DEFAULT_TIMESTAMP_SECONDS = () => Math.floor(Date.now() / 1000);

function requireInternalApiSecret() {
    const secret = process.env.YARA_INTERNAL_API_SECRET;
    if (!secret) {
        throw new Error(
            "YARA_INTERNAL_API_SECRET não está configurado no servidor frontend.",
        );
    }
    return secret;
}

export function createInternalApiAuthHeaders(
    method: string,
    targetUrl: URL,
    body?: BodyInit | null,
    timestamp = DEFAULT_TIMESTAMP_SECONDS(),
) {
    const pathWithQuery = `${targetUrl.pathname}${targetUrl.search}`;
    const signature = internalApiAuthCore.computeSignature(
        requireInternalApiSecret(),
        method,
        pathWithQuery,
        timestamp,
        body,
    );

    return {
        [internalApiAuthCore.TIMESTAMP_HEADER]: String(timestamp),
        [internalApiAuthCore.SIGNATURE_HEADER]: signature,
    };
}

export async function internalApiFetch(
    input: string | URL,
    init: RequestInit = {},
) {
    const targetUrl = input instanceof URL ? input : new URL(input);
    const method = (init.method ?? "GET").toUpperCase();
    const body = internalApiAuthCore.bodyToBuffer(init.body);
    const headers = new Headers(init.headers);
    const authHeaders = createInternalApiAuthHeaders(
        method,
        targetUrl,
        body,
    );

    for (const [name, value] of Object.entries(authHeaders)) {
        headers.set(name, value);
    }

    return fetch(targetUrl, {
        ...init,
        method,
        headers,
        body: method === "GET" || method === "HEAD" ? undefined : body,
    });
}
