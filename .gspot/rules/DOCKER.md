# Docker

Read this rule when you change a Dockerfile, a Compose file, or `.dockerignore`.

## Image inputs

Select a base image that supports the application's runtime, target architecture, system libraries, and certificate
requirements. Tags can change, so pin a reviewed digest when the build requires immutable input, and keep an update
process for security fixes.

Use a supported runtime release. For compiled modules, keep the build and runtime operating system, libc, and
architecture compatible.

## Build and runtime stages

Keep build-only compilers, test dependencies, and package caches out of the final image. The final image keeps
interpreted source, declared debug artifacts, and any other file the runtime reads. Keep private source maps out of
publicly served assets. When compilation or dependency preparation needs tools the runtime does not, a multi-stage build
copies only the runtime inputs into the final stage. Never copy host `node_modules` into a Linux image. The final image
holds a package-manager binary only when the runtime uses it.

## Package installation and downloads

hadolint and Trivy report tags, pins, cache cleanup, and command form. Also apply these requirements:

- Refresh repository metadata and install packages in the same `RUN`, so a stale cache cannot pick an unintended
  version.
- Refresh base images for operating-system fixes. A targeted package upgrade needs an explicit dependency change, never
  an unbounded distribution upgrade in every build.

## Build context and ignore files

The context holds only the files the build needs, and `.dockerignore` changes with every Dockerfile that uses it.

## Build secrets

Use BuildKit secret mounts for private registry authentication and other build credentials. Read the secret only inside
the `RUN` instruction that requires it. Copying it into a layer keeps it in image history even after a later step
removes it.

## Shell and process behavior

Match `RUN` syntax to the configured shell; the default one does not run Bash. A required entrypoint script validates
configuration and uses `exec` for its final handoff. A documented process supervisor forwards signals and reaps its
children, and no init wrapper hides missing shutdown behavior in the application.

The application's shutdown limit fits the orchestrator's grace period.

## Runtime

- The final stage runs as a numeric user other than root, such as `USER 1000:1000`, the uid and gid of the `node`
  user in the Node.js images.
- Durable state lives in explicit volumes or external storage. Environment-specific values arrive at runtime. A
  production Node.js service sets `NODE_ENV=production` where the runtime expects it.
- Expose only the required ports, and bind private local services to localhost. Never add Linux capabilities, public
  debug ports, or disabled TLS verification to make a build or service work.
- Resource limits fit the deployment and leave room for off-heap memory, buffers, and runtime overhead beyond the
  language heap. Ask the user for memory measurements before changing a limit when the task has none.

## Compose

Compose declares the wiring: ports, volumes, secrets, resource limits, health checks, restart policy, and dependencies.
Behavior stays in the application. `depends_on` orders startup, with the health condition when a service needs another
one ready. Never bind-mount development source or host dependencies into a production container.
