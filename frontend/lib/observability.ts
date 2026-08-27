import "server-only";

import observabilityCore from "./observability-core.cjs";

export const REQUEST_ID_HEADER = observabilityCore.REQUEST_ID_HEADER;

export function requestId(value?: string | null) {
    return observabilityCore.normalizeRequestId(value);
}

export function errorPayload(code: string, message: string, id: string) {
    return observabilityCore.errorPayload(code, message, id);
}

export function publicErrorResponse(code: string, message: string, id: string, status: number) {
    return Response.json(errorPayload(code, message, id), {
        status,
        headers: { "X-Request-ID": id },
    });
}

export function logRequest(fields: {
    requestId: string;
    method: string;
    path: string;
    status: number;
    durationMs: number;
    errorCode?: string | null;
}) {
    // Não adicionar headers, corpos, URLs assinadas ou metadata a este evento.
    const event = {
        timestamp: new Date().toISOString(),
        level: fields.status >= 500 ? "error" : fields.status >= 400 ? "warning" : "info",
        service: "yara-nextjs",
        request_id: fields.requestId,
        method: fields.method,
        path: fields.path,
        status: fields.status,
        duration_ms: Number(fields.durationMs.toFixed(3)),
        error_code: fields.errorCode ?? null,
    };
    console.info(JSON.stringify(event));
}
