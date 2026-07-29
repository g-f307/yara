"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
    buildCanonicalRequest,
    computeSignature,
    sha256Hex,
} = require("./internal-api-auth-core.cjs");

const vectorPath = path.resolve(
    __dirname,
    "../../tests/fixtures/internal_api_hmac.json",
);
const vector = JSON.parse(fs.readFileSync(vectorPath, "utf8"));

test("produces the shared SHA-256 body hash", () => {
    assert.equal(sha256Hex(vector.body), vector.body_sha256);
});

test("builds the documented canonical request", () => {
    assert.equal(
        buildCanonicalRequest(
            vector.method,
            vector.path_with_query,
            vector.timestamp,
            vector.body,
        ),
        [
            vector.method,
            vector.path_with_query,
            String(vector.timestamp),
            vector.body_sha256,
        ].join("\n"),
    );
});

test("produces the shared HMAC-SHA256 signature", () => {
    assert.equal(
        computeSignature(
            vector.secret,
            vector.method,
            vector.path_with_query,
            vector.timestamp,
            vector.body,
        ),
        vector.signature,
    );
});

test("changes the signature when signed request data changes", () => {
    const changes = [
        ["GET", vector.path_with_query, vector.body],
        [vector.method, "/api/alpha/analyze?mode=other", vector.body],
        [vector.method, vector.path_with_query, `${vector.body} `],
    ];

    for (const [method, pathWithQuery, body] of changes) {
        assert.notEqual(
            computeSignature(
                vector.secret,
                method,
                pathWithQuery,
                vector.timestamp,
                body,
            ),
            vector.signature,
        );
    }
});
