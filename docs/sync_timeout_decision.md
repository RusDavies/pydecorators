# Sync Timeout Decision

`@timeout` remains async-only for the first public release.

## Decision

Do not add synchronous timeout support without a separate explicit design, because Python cannot safely cancel arbitrary synchronous code in a portable library decorator.

## Constraints any future sync design must state

- Platform support: whether the implementation is Unix-only, CPython-only, main-thread-only, or event-loop-specific.
- Cancellation semantics: whether work is actually stopped or merely abandoned while it continues elsewhere.
- Resource ownership: what happens to locks, files, sockets, transactions, and partially mutated state when a timeout fires.
- Thread/process behavior: whether the design uses worker threads, subprocesses, signals, or caller-provided executors.
- Cleanup expectations: how callers should make timed-out work idempotent and recoverable.

## Rejected first-release approaches

- `signal.alarm`: process-global, Unix-specific, main-thread-only, and rude inside a library.
- Worker threads: the caller may see a timeout while the original function keeps running, which is not cancellation; it is denial with extra stack frames.
- Subprocess wrappers: safer isolation but too heavy and opinionated for a decorator in this package’s first release.

Until those constraints are worth exposing as public API, decorating a synchronous callable raises `ConfigurationError`.
