# Logging

Read this rule when you add or change logging.

## One logger

- One logging module per process, configured at the entry point: level, format, redaction, transports.
- Feature code gets a logger from that module. It never instantiates, configures, or adds transports.
- A service logs to stdout. Configure other transports at the logger.

## Levels

- `debug`: noisy diagnostic detail, off in production.
- `info`: normal lifecycle events and status.
- `warn`: degraded, retryable, or unexpected but survivable conditions.
- `error`: an operation failed and no caller recovered.
- `fatal`: the process cannot go on and stops.
- Do not add custom levels.

## Structure

- Write a stable, human-readable message string that describes the event. Values go in structured fields, never
  interpolated into the message.
- Preserve declared event names and field keys. Before you rename one, tell the user because dashboards and alerts may
  read it.
- Include the trace ID of the request when one exists.
- Use stable names for request, correlation, provider request, operation, resource, and safe user IDs. Propagate them to
  provider calls when supported.
- Put an error object in the field the logger serializes errors from, so it keeps the stack and cause.
- Summarize: counts, IDs, statuses, provider names, and durations. No large, deeply nested, or expensive-to-compute
  fields.
- Do not compute expensive log arguments when the logger disables the level.

## Sensitive values

Follow SECRETS.md. Never log personal data, raw user content, full request or response bodies, provider payloads, or
database rows.

Redaction lives in the logging module. When a new sensitive key can reach logs, update the redaction list; do not filter
at one call site.

```ts
// Bad.
logger.info({ headers: req.headers }, 'Incoming request');

// Good.
logger.info({ path: req.path, method: req.method, requestId }, 'Incoming request');
```

A logging test asserts the fields and redaction, not that the logger ran.
