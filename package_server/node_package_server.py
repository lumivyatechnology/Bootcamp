#!/usr/bin/env python3
"""Build and serve a local npm registry cache for bootcamp installs."""

from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
REGISTRY_DIR = ROOT / "node_registry"
STORAGE_DIR = REGISTRY_DIR / "storage"
CONFIG_FILE = REGISTRY_DIR / "verdaccio.yaml"


def run_command(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


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


def write_config(listen_host: str, listen_port: int) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        f"""storage: {STORAGE_DIR.as_posix()}
listen: {listen_host}:{listen_port}
uplinks:
  npmjs:
    url: https://registry.npmjs.org/
packages:
  '@*/*':
    access: $all
    publish: $all
    proxy: npmjs
  '**':
    access: $all
    publish: $all
    proxy: npmjs
logs:
  - {{type: stdout, format: pretty, level: http}}
""",
        encoding="utf-8",
    )


def verdaccio_command(config_file: Path, listen_host: str, listen_port: int) -> list[str]:
    return [
        "npx",
        "--yes",
        "verdaccio@6",
        "--config",
        str(config_file),
        "--listen",
        f"{listen_host}:{listen_port}",
    ]


def wait_for_registry(base_url: str, timeout: int = 60) -> None:
    ping_url = f"{base_url}/-/ping"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(ping_url, timeout=3) as response:
                if response.status == 200:
                    return
        except urllib.error.URLError:
            time.sleep(1)

    raise TimeoutError(f"Verdaccio did not become ready at {ping_url}")


def warm_registry(base_url: str) -> None:
    package_json = FRONTEND_DIR / "package.json"
    package_lock = FRONTEND_DIR / "package-lock.json"

    if not package_json.exists() or not package_lock.exists():
        raise FileNotFoundError("frontend/package.json and package-lock.json are required.")

    with tempfile.TemporaryDirectory(prefix="bootcamp-node-warm-") as temp_dir:
        temp_path = Path(temp_dir)
        shutil.copy2(package_json, temp_path / "package.json")
        shutil.copy2(package_lock, temp_path / "package-lock.json")
        try:
            run_command(
                [
                    "npm",
                    "ci",
                    "--ignore-scripts",
                    "--prefer-offline",
                    "--registry",
                    base_url,
                ],
                cwd=temp_path,
            )
        except subprocess.CalledProcessError as error:
            print(f"Warning: npm cache warm-up failed, serving existing registry data if available: {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare and serve a local npm registry cache.")
    parser.add_argument("--port", type=int, default=4873, help="Port to serve on")
    parser.add_argument("--bind", default="0.0.0.0", help="Interface to bind to")
    parser.add_argument(
        "--no-serve",
        action="store_true",
        help="Build the cache and exit without leaving the registry running",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Clear the local registry storage before warming it",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if shutil.which("npm") is None:
        raise RuntimeError("npm is required but was not found on PATH.")
    if shutil.which("npx") is None:
        raise RuntimeError("npx is required but was not found on PATH.")

    if args.refresh and STORAGE_DIR.exists():
        shutil.rmtree(STORAGE_DIR)

    write_config(listen_host=args.bind, listen_port=args.port)
    registry_host = "127.0.0.1" if args.bind == "0.0.0.0" else args.bind
    registry_url = f"http://{registry_host}:{args.port}"
    process = subprocess.Popen(
        verdaccio_command(CONFIG_FILE, args.bind, args.port),
        cwd=ROOT,
    )

    try:
        wait_for_registry(registry_url)
        warm_registry(registry_url)

        if args.no_serve:
            print(f"npm cache prepared at: {STORAGE_DIR}")
            print(f"Verdaccio config: {CONFIG_FILE}")
            return

        host = get_advertised_host(args.bind)
        print()
        print(f"Registry ready: http://{host}:{args.port}/")
        print("Participant install example:")
        print(f'  npm config set registry "http://{host}:{args.port}/"')
        print("  npm install")
        print()
        print("Press Ctrl+C to stop.")
        process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
