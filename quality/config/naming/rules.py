"""Naming rule runner policy."""

from quality.config.repository.paths import PYTHON_SOURCE_DIRS

SINGLE_FILE_SOURCE_ROOTS = {
    "src",
    "quality",
}

SCOPE_SOURCE_DIRS = {
    "all": PYTHON_SOURCE_DIRS,
    "python": PYTHON_SOURCE_DIRS,
    "quality": ("quality",),
    "src": ("src",),
    "tests": ("tests",),
    "docker": ("docker",),
}

PYTHON_SCOPES = {
    "all",
    "python",
    "quality",
    "src",
    "tests",
    "docker",
    "staged",
}

SHELL_SCOPES = {
    "all",
    "shell",
    "hooks",
    "mise",
    "quality",
    "scripts",
    "docker",
    "staged",
}

DIGIT_CHECK_CATEGORIES = {
    "directories",
    "files",
}

VAGUE_SCRIPT_NAMES = {
    "common",
    "helper",
    "helpers",
    "utils",
    "util",
}
