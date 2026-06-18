#!/usr/bin/env python3
"""Build and serve a local Python package cache for bootcamp installs."""

from __future__ import annotations

import argparse
import http.server
import shutil
import socket
import subprocess
import sys
import tempfile
import venv
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
BACKEND_DIR = REPO_ROOT / "backend"
WHEELHOUSE_DIR = ROOT / "wheelhouse"
REQUIREMENTS_FILE = ROOT / ".bootcamp-requirements.txt"
SUPPLEMENTAL_PACKAGES = (
    "numpy",
    "python-dotenv",
    "itemadapter",
)


def run_command(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def create_temp_venv() -> Path:
    venv_dir = Path(tempfile.mkdtemp(prefix="bootcamp-wheelhouse-venv-"))
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(venv_dir)
    return venv_dir


def get_advertised_host(bind: str) -> str:
    if bind != "0.0.0.0":
        return bind

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        probe.close()


def export_requirements(include_all_groups: bool) -> Path:
    if not (BACKEND_DIR / "pyproject.toml").exists():
        raise FileNotFoundError("backend/pyproject.toml not found.")

    command = [
        "uv",
        "--project",
        str(BACKEND_DIR),
        "export",
        "--format",
        "requirements.txt",
        "--no-dev",
        "--no-header",
        "--no-annotate",
        "--no-editable",
        "--emit-index-url",
        "--emit-find-links",
        "--output-file",
        str(REQUIREMENTS_FILE),
        "--frozen",
    ]

    if include_all_groups:
        command.append("--all-groups")

    run_command(command, cwd=REPO_ROOT)

    with REQUIREMENTS_FILE.open("a", encoding="utf-8") as handle:
        handle.write("\n# Supplemental packages referenced by repository code and notebooks\n")
        for package in SUPPLEMENTAL_PACKAGES:
            handle.write(f"{package}\n")

    return REQUIREMENTS_FILE


def download_packages(requirements_file: Path, refresh: bool, pip_python: Path) -> None:
    WHEELHOUSE_DIR.mkdir(exist_ok=True)

    command = [
        str(pip_python),
        "-m",
        "pip",
        "download",
        "--ignore-requires-python",
        "-r",
        str(requirements_file),
        "-d",
        str(WHEELHOUSE_DIR),
    ]

    if refresh:
        command.append("--no-cache-dir")

    try:
        run_command(command, cwd=ROOT)
    except subprocess.CalledProcessError as error:
        print(f"Warning: package download failed, serving existing cache if available: {error}")


def start_server(port: int, bind: str) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(WHEELHOUSE_DIR))
    server = http.server.ThreadingHTTPServer((bind, port), handler)
    host = get_advertised_host(bind)

    print()
    print(f"Wheelhouse ready: {WHEELHOUSE_DIR}")
    print(f"Serving packages at: http://{bind}:{port}/")
    print()
    print("Participant install example:")
    print(f'  PIP_NO_INDEX=1 PIP_FIND_LINKS="http://{host}:{port}/" \\')
    print(f"    pip install -r {REQUIREMENTS_FILE.name}")
    print()
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare and serve a local Python package cache for the bootcamp."
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on")
    parser.add_argument(
        "--bind",
        default="0.0.0.0",
        help="Interface to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--no-serve",
        action="store_true",
        help="Build the cache and exit without starting the server",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore pip cache while downloading packages",
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Export only the backend core dependencies and skip dependency groups",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if shutil.which("uv") is None:
        raise RuntimeError("uv is required but was not found on PATH.")

    requirements_file = export_requirements(include_all_groups=not args.core_only)
    temp_venv = create_temp_venv()
    try:
        pip_python = temp_venv / ("Scripts" if sys.platform == "win32" else "bin") / "python"
        download_packages(
            requirements_file=requirements_file,
            refresh=args.refresh,
            pip_python=pip_python,
        )
    finally:
        shutil.rmtree(temp_venv, ignore_errors=True)

    if args.no_serve:
        print(f"Cache prepared at: {WHEELHOUSE_DIR}")
        print(f"Requirements exported to: {REQUIREMENTS_FILE}")
        print("Supplemental packages included:")
        for package in SUPPLEMENTAL_PACKAGES:
            print(f"  - {package}")
        return

    start_server(port=args.port, bind=args.bind)


if __name__ == "__main__":
    main()
