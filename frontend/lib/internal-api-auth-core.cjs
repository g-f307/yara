"use strict";

const { createHash, createHmac } = require("node:crypto");

const TIMESTAMP_HEADER = "X-Yara-Timestamp";
const SIGNATURE_HEADER = "X-Yara-Signature";

function bodyToBuffer(body) {
    if (body == null) return Buffer.alloc(0);
    if (Buffer.isBuffer(body)) return body;
    if (typeof body === "string") return Buffer.from(body, "utf8");
    if (body instanceof ArrayBuffer) return Buffer.from(body);
    if (ArrayBuffer.isView(body)) {
        return Buffer.from(body.buffer, body.byteOffset, body.byteLength);
    }
    if (body instanceof URLSearchParams) return Buffer.from(body.toString(), "utf8");

    throw new TypeError("Tipo de corpo não suportado para assinatura interna.");
}

function sha256Hex(body) {
    return createHash("sha256").update(bodyToBuffer(body)).digest("hex");
}

function buildCanonicalRequest(method, pathWithQuery, timestamp, body) {
    return [
        method.toUpperCase(),
        pathWithQuery,
        String(timestamp),
        sha256Hex(body),
    ].join("\n");
}

function computeSignature(secret, method, pathWithQuery, timestamp, body) {
    const canonical = buildCanonicalRequest(
        method,
        pathWithQuery,
        timestamp,
        body,
    );
    return createHmac("sha256", secret).update(canonical, "utf8").digest("hex");
}

module.exports = {
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    bodyToBuffer,
    buildCanonicalRequest,
    computeSignature,
    sha256Hex,
};
