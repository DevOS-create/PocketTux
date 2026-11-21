#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    sys.stderr.write("Python 3.9 or newer is required.\n")
    raise SystemExit(1)

VERSION = "0.1.0-beta"

USE_COLOR = sys.stdout.isatty()
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".DS_Store")


def paint(code, message):
    return f"\033[{code}m{message}\033[0m" if USE_COLOR else str(message)


def log(message):
    print(paint("1;36", message))


def success(message):
    print(paint("1;32", message))


def warning(message):
    print(paint("1;33", message), file=sys.stderr)


def fail(message):
    print(paint("1;31", message), file=sys.stderr)
    raise SystemExit(1)


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy_item(source, destination):
    if source.is_dir():
        remove_path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, symlinks=True, ignore=IGNORE)
    elif source.is_file():
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def write_launcher(launcher, app_dir, prefix, user_home):
    content = f"""#!{sys.executable}
import os
import sys

sys.path.insert(0, {str(app_dir)!r})
os.environ.setdefault("POCKETTUX_PREFIX", {str(prefix)!r})
os.environ.setdefault("POCKETTUX_HOME", {str(user_home)!r})

from pockettux.cli import main

if __name__ == "__main__":
    sys.exit(main())
"""
    temp = launcher.with_name(f".{launcher.name}.tmp")
    temp.write_text(content, encoding="utf-8")
    temp.chmod(0o755)
    os.replace(temp, launcher)


def run_build(root, prefix, user_home):
    build_script = root / "build.sh"
    if not build_script.is_file():
        return
    log("Building native components...")
    env = {
        **os.environ,
        "PREFIX": str(prefix),
        "POCKETTUX_PREFIX": str(prefix),
        "POCKETTUX_HOME": str(user_home),
        "POCKETTUX_VERSION": VERSION,
    }
    try:
        result = subprocess.run(
            ["bash", str(build_script)],
            cwd=root,
            env=env,
            check=False,
        )
    except OSError as exc:
        warning(f"Native build could not start: {exc}")
        return
    if result.returncode != 0:
        warning("Native build failed; continuing with Python components.")


def install(args):
    root = Path(__file__).resolve().parent

    if not args.prefix:
        fail("Invalid installation PREFIX.")

    prefix = Path(args.prefix).expanduser().resolve()
    user_home = Path(args.home).expanduser().resolve()

    if not prefix.is_dir() or not os.access(prefix, os.W_OK):
        fail(f"Invalid or non-writable PREFIX: {prefix}")

    app_source = root / "pockettux"

    if not app_source.is_dir():
        fail("PocketTux application directory is missing.")
    if not (app_source / "__init__.py").is_file():
        fail("Application package is incomplete.")
    if not (app_source / "cli.py").is_file():
        fail("Application entry point pockettux/cli.py is missing.")

    log("Preparing installation directories...")

    bin_dir = prefix / "bin"
    lib_dir = prefix / "lib" / "pockettux"
    app_dir = lib_dir / "app"
    native_dir = lib_dir / "native"
    share_dir = prefix / "share" / "pockettux"
    config_dir = user_home / "config"
    data_dir = user_home / "data"
    cache_dir = user_home / "cache"

    for directory in (
        bin_dir, app_dir, native_dir, share_dir,
        user_home, config_dir, data_dir, cache_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    if not args.no_build:
        run_build(root, prefix, user_home)

    log("Installing Python application...")

    copy_item(app_source, app_dir / "pockettux")

    built_native = root / "build" / "native"

    if built_native.is_dir():
        log("Installing native components...")
        for item in built_native.iterdir():
            copy_item(item, native_dir / item.name)

    log("Installing project resources...")

    for name in ("docs", "examples", "assets", "scripts", "native"):
        source = root / name
        if source.exists():
            copy_item(source, share_dir / name)

    for name in ("README.md", "LICENSE", "CHANGELOG.md"):
        source = root / name
        if source.is_file():
            copy_item(source, share_dir / name)

    log("Creating PocketTux launcher...")

    launcher = bin_dir / "pockettux"
    write_launcher(launcher, app_dir, prefix, user_home)

    log("Verifying installation...")

    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        fail("Launcher creation failed.")
    if not (app_dir / "pockettux" / "cli.py").is_file():
        fail("Installed application verification failed.")

    success(f"PocketTux {VERSION} installed successfully.")
    print(f"Executable:  {launcher}")
    print(f"Application: {app_dir}")
    print(f"Resources:   {share_dir}")
    print(f"User data:   {user_home}")
    print()
    print("Launch PocketTux with: pockettux")


def main():
    parser = argparse.ArgumentParser(description="PocketTux Python Installer")
    parser.add_argument("--prefix", default=os.environ.get("PREFIX"))
    parser.add_argument(
        "--home",
        default=os.environ.get(
            "POCKETTUX_HOME",
            str(Path.home() / ".pockettux"),
        ),
    )
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    try:
        install(args)
    except KeyboardInterrupt:
        fail("Installation interrupted.")
    except (OSError, shutil.Error) as exc:
        fail(f"Installation failed: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())