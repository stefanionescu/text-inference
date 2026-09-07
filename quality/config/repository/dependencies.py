"""Dependency ownership policy."""

PROJECT_METADATA_FILE = "pyproject.toml"
LOCK_FILE = "uv.lock"
PROJECT_PACKAGE_NAME = "text-inference"
RUNTIME_EXTRAS = ("local", "vllm", "trt", "llmcompressor")
DEV_DEPENDENCY_GROUP = "dev"

PROJECT_SECTION = "project"
OPTIONAL_DEPENDENCIES_SECTION = "optional-dependencies"
DEPENDENCY_GROUPS_SECTION = "dependency-groups"
LOCK_PACKAGE_SECTION = "package"
PACKAGE_NAME_FIELD = "name"

ROOT_REQUIREMENTS_GLOB = "requirements*.txt"
EXPORT_TASK = ".mise/tasks/deps/export"
EXPORT_SCAN_ROOTS = (
    ".mise/tasks",
    "scripts",
    "docker",
)
INSTALL_COMMAND_SCAN_ROOTS = (
    "docker",
    "scripts",
)

REQUIREMENTS_EXPORT_COMMAND = "uv pip compile"
DIRECT_PIP_INSTALL_PATTERN = r"(^|[\s;&|({])(?:python[0-9.]*\s+-m\s+)?pip\s+install\b"
UV_PIP_INSTALL = "uv pip install"
UV_PIP_WRAPPER = "uv_run pip install"
ALLOWED_UV_PIP_PATHS = (
    "docker/vllm/Dockerfile",
    "docker/trt/Dockerfile",
    "scripts/lib/deps/uv/environment.sh",
)

POLICY_FILE_SUFFIXES = {".sh", ".py", ".md", ".toml"}
POLICY_FILE_NAMES = {"Dockerfile", ".dockerignore"}
POLICY_FILE_IGNORED_PARTS = {".git", ".venv", ".venv-quant", "node_modules"}
