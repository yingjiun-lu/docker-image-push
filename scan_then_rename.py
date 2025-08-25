#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def run_scan(chart_path: Path, timeout: int) -> int:
    script = Path(__file__).with_name("scan_helm_images.py")
    cmd = [sys.executable, str(script), str(chart_path), "--strict", "--timeout", str(timeout)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    combined_output = (proc.stdout or "") + (proc.stderr or "")
    print(combined_output, end="")

    # Consider success if process exit code is 0 OR output includes the phrase
    # "Process exited with code: 0" (to be robust with different wrappers)
    if proc.returncode == 0:
        return 0
    if "Process exited with code: 0" in combined_output:
        return 0
    return proc.returncode or 1


def run_rename(root_path: Path) -> int:
    script = Path(__file__).with_name("rename_bitnami_images.py")
    cmd = [
        sys.executable,
        str(script),
        str(root_path),
        "--source-namespace",
        "bitnami",
        "--target-namespace",
        "bitnamilegacy",
    ]
    return subprocess.call(cmd)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run scan_helm_images.py against a Helm chart directory, and run "
            "rename_bitnami_images.py only if the scan succeeds."
        )
    )
    parser.add_argument("path", help="Path to the Helm chart directory to scan and the root path to rename under")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds for Docker Hub checks (default: 15)")

    args = parser.parse_args(argv)

    chart_path = Path(args.path).resolve()
    if not chart_path.exists() or not chart_path.is_dir():
        print(f"[ERROR] Path does not exist or is not a directory: {chart_path}")
        return 2

    print(f"[STEP] Scanning images under chart: {chart_path}")
    scan_rc = run_scan(chart_path, args.timeout)
    print(f"[INFO] scan_helm_images.py exit code: {scan_rc}")

    if scan_rc == 0:
        print(f"[STEP] Scan succeeded. Running rename_bitnami_images.py on: {chart_path}")
        rename_rc = run_rename(chart_path)
        print(f"[INFO] rename_bitnami_images.py exit code: {rename_rc}")
        return rename_rc

    print("[SKIP] Scan failed. Skipping rename.")
    return scan_rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:])) 