"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { errorPayload, normalizeRequestId } = require("./observability-core.cjs");

test("preserves a valid correlation ID", () => {
    const id = "550e8400-e29b-41d4-a716-446655440000";
    assert.equal(normalizeRequestId(id), id);
});

test("replaces invalid or oversized correlation IDs", () => {
    for (const candidate of ["invalid", "x".repeat(200), null]) {
        const generated = normalizeRequestId(candidate);
        assert.match(generated, /^[0-9a-f-]{36}$/);
        assert.notEqual(generated, candidate);
    }
});

test("builds the public error contract", () => {
    const id = "550e8400-e29b-41d4-a716-446655440000";
    assert.deepEqual(errorPayload("INVALID_REQUEST", "Requisição inválida.", id), {
        error: { code: "INVALID_REQUEST", message: "Requisição inválida.", request_id: id },
    });
});
