"""Repository path policy for quality tooling."""

LICENSE_POLICY_FILE = "quality/config/repository/licenses/policy.json"

PYTHON_SOURCE_DIRS = (
    "config",
    "src",
    "tests",
    "quality",
    "docker",
)

PYTHON_RUNTIME_DIRS = (
    "config",
    "src",
    "docker",
)

SHELL_SOURCE_DIRS = (
    ".githooks",
    ".mise/tasks",
    "scripts",
    "docker",
    "quality",
)

CONFIG_SOURCE_DIRS = (
    "config",
    "quality/config",
)

SHELL_TASK_PREFIXES = (
    ".mise/tasks/",
    ".githooks/",
)

SHELL_SCOPE_PREFIXES = {
    "all": ("",),
    "shell": ("scripts/", "docker/", "quality/"),
    "hooks": (".githooks/",),
    "mise": (".mise/tasks/",),
    "quality": ("quality/",),
    "scripts": ("scripts/",),
    "docker": ("docker/",),
}

QUALITY_EXCLUDED_DIRS = {
    ".artifacts",
    ".cache",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-quant",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

FUNCTION_POLICY_EXCLUDED_DIRS = {
    ".artifacts",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-quant",
    "__pycache__",
    "models",
}
