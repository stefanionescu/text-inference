# FastAPI

Read this rule when you change a FastAPI application.

These rules target FastAPI with Pydantic v2.

## Structure

Keep business logic out of path operations: a path operation turns HTTP input into an application call, and its result
into a response. One main module creates the `FastAPI` object and wires routers, global dependencies, middleware,
exception handlers, and startup. Routers group related operations under a prefix that does not end in `/`, and imports
use their domain, `items.router` and `users.router`.

## Parameters

Declare each parameter with `Annotated[..., Query(...)]`, `Path`, `Body`, `Header`, `Cookie`, `Form`, `File`, or
`Depends`. A plain scalar supplies a query parameter. A parameter without a default requires a value, even when it
accepts `None`. Put constraints such as `max_length` or `ge` at the boundary when the public interface requires them.
Use a dependency for a check that needs a database or authorization state, not a validator. Declare fixed routes such as
`/users/me` before `/users/{user_id}`, and group pagination or filter parameters into a query model with
`extra="forbid"`.

Forms need `python-multipart`, and one operation never mixes JSON body fields with form data or files. Uploads arrive as
`UploadFile`, bounded in count and size; `bytes` holds only small values. Never use a filename as a filesystem path or
log uploaded contents. A content type proves nothing about safety.

## Schemas and responses

Pydantic models define the schemas where data enters or leaves. Use separate classes for create, read, and update shapes
when their fields differ. Never return an input with passwords or tokens as the response. Known JSON shapes use nested
models with typed containers. Use timezone-aware instants across a boundary, and `Decimal` for money. A partial update
reads `model_dump(exclude_unset=True)`, merges with the stored value, and validates the whole model;
`model_copy(update=...)` skips validation.

The return type defines the public schema; `response_model` serves a returned object of another shape. Filter fields
with a dedicated output model, never with `response_model_exclude`, which still documents the whole schema. A response
validation failure shows a server bug. Fix the data or the schema.

## Status codes and errors

Put a non-default success code in the decorator, with a `fastapi.status` constant. Raise `HTTPException` rather than
returning it. Its `detail` supplies a public error message. Never put the text of a caught exception in `detail`; log
it, and return a stable message. Existence and authorization checks fail the same way, so responses do not reveal a
private resource. Return the standard error shape from global exception handlers, and never echo the request body of a
validation failure.

## Runtime

- Declare a path operation or dependency `async def` when it awaits async libraries, and `def` when it calls blocking
  code. A blocking call inside `async def` stalls the event loop. Run CPU-heavy work in a worker process, not in
  `async def`.
- Dependencies carry request-scoped concerns: authentication, sessions, pagination, and reusable validation. A `yield`
  dependency owns one resource, cleans up in `finally`, and re-raises what it catches.
- Use the security utilities for authentication that appears in OpenAPI. A JSON Web Token (JWT) verifier allows an
  explicit algorithm list and requires `exp` and `sub`.
- `BackgroundTasks` runs small follow-up jobs after the response; durable or heavy work goes to a queue. Keep only
  cross-cutting HTTP behavior in middleware; the one added last runs outermost.
- Turn OpenAPI and the interactive docs off unless a typed setting turns them on, and the schema exposes no internal or
  admin routes.

## Testing

Tests cover the HTTP contract through the test client: status codes, bodies, headers, and authentication. Replace
external systems with dependency overrides at the application boundary.
