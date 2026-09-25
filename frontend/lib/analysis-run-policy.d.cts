declare const policy: {
  TRANSITIONS: Readonly<Record<string, readonly string[]>>;
  TERMINAL_STATES: readonly string[];
  canTransition(from: string, to: string): boolean;
  isTerminal(state: string): boolean;
  assertTransition(from: string, to: string): void;
};
export = policy;
