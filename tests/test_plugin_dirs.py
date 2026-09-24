"""Tests for the conventional repository plugin directories."""

import importlib
import sys
from pathlib import Path


def test_plugin_directories_exist() -> None:
    root = Path(__file__).resolve().parent.parent
    for package in ("plugins/core", "plugins/builtin"):
        package_dir = root / package
        assert package_dir.is_dir(), f"missing directory: {package}"
        assert (package_dir / "__init__.py").is_file(), (
            f"missing package marker: {package}/__init__.py"
        )


def test_plugin_packages_import_cleanly() -> None:
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    added = root_str not in sys.path
    if added:
        sys.path.insert(0, root_str)
    try:
        core = importlib.import_module("plugins.core")
        builtin = importlib.import_module("plugins.builtin")
    finally:
        if added:
            sys.path.remove(root_str)
    assert hasattr(core, "__path__")
    assert hasattr(builtin, "__path__")
