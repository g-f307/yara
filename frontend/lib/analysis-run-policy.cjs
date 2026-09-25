"use strict";

const TRANSITIONS = Object.freeze({
  REQUESTED: Object.freeze(["VALIDATING", "CANCELLED"]),
  VALIDATING: Object.freeze(["QUEUED", "FAILED", "CANCELLED"]),
  QUEUED: Object.freeze(["RUNNING", "FAILED", "CANCELLED"]),
  RUNNING: Object.freeze(["SUCCEEDED", "FAILED", "CANCELLED"]),
  SUCCEEDED: Object.freeze([]),
  FAILED: Object.freeze([]),
  CANCELLED: Object.freeze([]),
});

const TERMINAL_STATES = Object.freeze(["SUCCEEDED", "FAILED", "CANCELLED"]);

function canTransition(from, to) {
  return Boolean(TRANSITIONS[from]?.includes(to));
}

function isTerminal(state) {
  return TERMINAL_STATES.includes(state);
}

function assertTransition(from, to) {
  if (!canTransition(from, to)) throw new Error(`Transição inválida de ${from} para ${to}.`);
}

module.exports = { TRANSITIONS, TERMINAL_STATES, canTransition, isTerminal, assertTransition };
