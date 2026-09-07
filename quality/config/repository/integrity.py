"""Repository configuration-boundary policy."""

CONFIG_IMPORT_ROOTS = {
    "__future__",
    "collections.abc",
    "quality.config",
    "config",
    "src.state",
    "config.tests",
    "typing",
}

DECLARATIVE_EXCLUSIONS = ("config/tests/prompts/",)
