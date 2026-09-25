const test = require("node:test");
const assert = require("node:assert/strict");
const { canTransition, isTerminal, assertTransition } = require("./analysis-run-policy.cjs");

test("permite o fluxo síncrono completo", () => {
  assert.equal(canTransition("REQUESTED", "VALIDATING"), true);
  assert.equal(canTransition("VALIDATING", "QUEUED"), true);
  assert.equal(canTransition("QUEUED", "RUNNING"), true);
  assert.equal(canTransition("RUNNING", "SUCCEEDED"), true);
});

test("permite cancelamento somente antes da terminalização", () => {
  for (const state of ["REQUESTED", "VALIDATING", "QUEUED", "RUNNING"]) {
    assert.equal(canTransition(state, "CANCELLED"), true);
  }
  assert.equal(canTransition("SUCCEEDED", "CANCELLED"), false);
});

test("estados terminais não aceitam transições", () => {
  for (const state of ["SUCCEEDED", "FAILED", "CANCELLED"]) {
    assert.equal(isTerminal(state), true);
    assert.throws(() => assertTransition(state, "RUNNING"), /Transição inválida/);
  }
});

test("rejeita saltos e regressões de estado", () => {
  assert.throws(() => assertTransition("REQUESTED", "RUNNING"), /Transição inválida/);
  assert.throws(() => assertTransition("RUNNING", "QUEUED"), /Transição inválida/);
});
