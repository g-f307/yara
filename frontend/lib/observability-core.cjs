"use strict";

const { randomUUID } = require("node:crypto");

const REQUEST_ID_HEADER = "x-request-id";
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function normalizeRequestId(value) {
    if (typeof value !== "string" || value.length > 36 || !UUID_PATTERN.test(value)) {
        return randomUUID();
    }
    return value.toLowerCase();
}

function errorPayload(code, message, requestId) {
    return { error: { code, message, request_id: requestId } };
}

module.exports = { REQUEST_ID_HEADER, normalizeRequestId, errorPayload };
