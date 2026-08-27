declare const observabilityCore: {
    REQUEST_ID_HEADER: "x-request-id";
    normalizeRequestId(value?: string | null): string;
    errorPayload(code: string, message: string, requestId: string): {
        error: { code: string; message: string; request_id: string };
    };
};

export = observabilityCore;
