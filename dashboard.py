#!/usr/bin/env python3
"""
One-click launcher for the Ultimate Macroeconomics Dashboard.

Usage:
    python dashboard.py

The script starts the Docker Compose stack, waits until the Streamlit
dashboard is healthy, and opens it in the default browser.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "http://localhost:8501"
HEALTH_URL = f"{URL}/_stcore/health"
POLL_SECONDS = 5


def fail(message: str) -> None:
    print(f"\nERROR: {message}")
    input("\nPress Enter to close...")
    raise SystemExit(1)


def run_compose(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        text=True,
        check=False,
    )


def main() -> None:
    print("=" * 60)
    print(" Ultimate Macroeconomics Dashboard")
    print("=" * 60)

    if not (ROOT / "docker-compose.yaml").is_file():
        fail("docker-compose.yaml was not found next to dashboard.py.")

    env_file = ROOT / ".env"
    env_example = ROOT / ".env.example"

    if not env_file.is_file():
        if not env_example.is_file():
            fail(
                ".env was not found, and .env.example is also missing. "
                "Restore the project configuration files and try again."
            )

        print("\nFirst-time setup detected.")
        print("Creating .env automatically from .env.example...")
        shutil.copy2(env_example, env_file)

        print(
            "\nYour .env file has been created successfully.\n"
            "Before the dashboard can start, open .env and replace the example "
            "values with your real configuration. At minimum, you will normally "
            "need valid values for OPENAI_API_KEY and FRED_API_KEY, plus secure "
            "passwords/secrets for the local services.\n"
            f"Configuration file: {env_file}\n"
        )

        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["notepad.exe", str(env_file)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(env_file)])
            else:
                subprocess.Popen(["xdg-open", str(env_file)])
        except OSError:
            pass

        input("Edit and save .env, then press Enter here to continue...")

    if shutil.which("docker") is None:
        fail("Docker was not found. Install Docker Desktop and try again.")

    version = run_compose("version")
    if version.returncode != 0:
        fail("Docker Compose is not available. Ensure Docker Desktop is running.")

    # If the dashboard is already healthy, simply bring it to the foreground.
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as response:
            if response.status == 200:
                print("\nDashboard is already running.")
                webbrowser.open(URL)
                return
    except (urllib.error.URLError, TimeoutError):
        pass

    print("\nStarting the dashboard stack...")
    result = run_compose("up", "-d", "--build")
    if result.returncode != 0:
        fail("Docker Compose could not start the stack.")

    print("\nServices are starting.")
    print("The first launch can take a long time because images, models, and")
    print("the initial datasets may need to be downloaded and processed.")
    print("This window will open the dashboard automatically when it is ready.")
    print("Press Ctrl+C if you only want to stop waiting; the Docker services")
    print("will continue running in the background.\n")

    while True:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as response:
                if response.status == 200:
                    print("\nDashboard is ready. Opening your browser...")
                    webbrowser.open(URL)
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        print("Waiting for http://localhost:8501 ...", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped waiting. The Docker services are still running.")
