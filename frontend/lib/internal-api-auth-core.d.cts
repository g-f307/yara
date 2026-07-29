declare const TIMESTAMP_HEADER: "X-Yara-Timestamp";
declare const SIGNATURE_HEADER: "X-Yara-Signature";

declare function bodyToBuffer(body?: BodyInit | null): Buffer;
declare function sha256Hex(body?: BodyInit | null): string;
declare function buildCanonicalRequest(
    method: string,
    pathWithQuery: string,
    timestamp: number | string,
    body?: BodyInit | null,
): string;
declare function computeSignature(
    secret: string,
    method: string,
    pathWithQuery: string,
    timestamp: number | string,
    body?: BodyInit | null,
): string;

declare const internalApiAuthCore: {
    TIMESTAMP_HEADER: typeof TIMESTAMP_HEADER;
    SIGNATURE_HEADER: typeof SIGNATURE_HEADER;
    bodyToBuffer: typeof bodyToBuffer;
    sha256Hex: typeof sha256Hex;
    buildCanonicalRequest: typeof buildCanonicalRequest;
    computeSignature: typeof computeSignature;
};

export = internalApiAuthCore;
