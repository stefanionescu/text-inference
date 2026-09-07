# Vendored Semgrep registry rules

The files under `vendor/` are snapshots returned by the Semgrep registry on
2026-07-17, with the local adjustment described below. They are used locally so
normal security scans perform no registry or other Semgrep network access. The
snapshot was captured with Semgrep CLI 1.152.0.

The Slack webhook rule in `vendor/secrets.yml` expresses its placeholder
exclusion as an equivalent regular expression. This keeps the placeholder
excluded without embedding a webhook-shaped URL that triggers push protection.
The SHA-256 values below describe the local files; ETags identify the registry
snapshots.

| Local file                 | Registry source                         | HTTP ETag                                      | SHA-256                                                            |
| -------------------------- | --------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------ |
| `vendor/python.yml`        | `https://semgrep.dev/c/p/python`        | `W/"0516aa8cc8c7e587c4b54621aa235b05f8b23c5d"` | `595e42e6cdb8afea3a6e6e2a1e686be0eb8a213e369f05cbb2cc3973ce21161d` |
| `vendor/bandit.yml`        | `https://semgrep.dev/c/p/bandit`        | `W/"5a780062e6fd4038d8e9c0725c05e56c4c3eb858"` | `f3bc01e39b3604b7397d65b7f06dcba3768e4188a5cac472e4635cab28d73d63` |
| `vendor/owasp-top-ten.yml` | `https://semgrep.dev/c/p/owasp-top-ten` | `W/"20cd8522a130bc09dbd281665a745268e569c241"` | `e180a256e7d762aff24be2d19b9deced05bce5eaf292b22427b1750db5901571` |
| `vendor/secrets.yml`       | `https://semgrep.dev/c/p/secrets`       | `W/"79990797fa9ef9d9c266fda33bcd96b336066412"` | `789ba3a7b3f7e92fc37db4bf5c80b1ffaae9047acc5d2a9b028a10e59102b5c6` |
| `vendor/bash.yml`          | `https://semgrep.dev/c/r/bash`          | `W/"37603ee734e38864e7ff8840c4af94938f27aa35"` | `5f5ab8e1df4e29551bb564ab6eeb6df9d40872b6c9566d4d1b0f86478f8db5ac` |

Each rule retains its registry metadata, including its source URL, rule/version
identifiers, and license notice. Most rules are licensed under the Semgrep
Rules License v1.0. The GitLab Bandit-derived rules marked `MIT` retain that
notice and are attributed to GitLab Inc. The applicable license texts are in
`LICENSE-SEMGREP-RULES.md` and `LICENSE-GITLAB-MIT.md`.
