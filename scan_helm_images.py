#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Set, Tuple
from loguru import logger

IMAGE_LINE_REGEX = re.compile(r"^\s*image:\s*[\"\']?([^\s\"\'#]+)", re.MULTILINE)


def render_chart_to_yaml(chart_path: Path, output_yaml_path: Path) -> None:
    parent_dir = chart_path.parent.resolve()
    chart_name = chart_path.name

    cmd = ["helm", "template", "--debug", chart_name]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(parent_dir),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        stdout = exc.stdout or ""
        raise RuntimeError(
            f"helm template failed with exit code {exc.returncode}.\nSTDERR:\n{stderr}\nSTDOUT:\n{stdout}"
        ) from exc

    output_yaml_path.write_text(result.stdout)


def extract_images_from_yaml(yaml_text: str) -> List[str]:
    matches = IMAGE_LINE_REGEX.findall(yaml_text)
    # Deduplicate while preserving order
    seen: Set[str] = set()
    images: List[str] = []
    for image in matches:
        if image not in seen:
            seen.add(image)
            images.append(image)
    return images


def split_repository_and_tag(image: str) -> Tuple[str, str]:
    # Skip digests like repo@sha256:...
    if "@" in image:
        raise ValueError(f"Image is a digest, not a tag: {image}")

    # Split on the last ':' to avoid registry ports
    if ":" not in image:
        # No explicit tag; default to 'latest' per Docker conventions
        return image, "latest"

    repository, tag = image.rsplit(":", 1)
    return repository, tag


def check_image(repository: str, tag: str, timeout: int) -> Tuple[bool, str]:
    if repository.startswith("docker.io/"):
        repository = repository[len("docker.io/"):]
    logger.info(f"Checking repository: {repository}, tag: {tag}")
    script_path = Path(__file__).with_name("check_docker_tag.py")
    cmd = [sys.executable, str(script_path), repository, tag, "--timeout", str(timeout)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    exists = proc.returncode == 0
    output = (proc.stdout or "").strip()
    return exists, output


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Render Helm chart and verify Docker image tags found in the rendered YAML.")
    parser.add_argument("chart_path", help="Path to the Helm chart directory to render")
    parser.add_argument("--yaml-out", dest="yaml_out", default=None, help="Optional path to write the rendered YAML. If not set, a temporary file is used.")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds for Docker Hub checks (default: 15)")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero if any image tag is missing.")

    args = parser.parse_args(argv)

    chart_path = Path(args.chart_path).resolve()
    if not chart_path.exists() or not chart_path.is_dir():
        logger.error(f"chart_path does not exist or is not a directory: {chart_path}")
        return 2

    if args.yaml_out:
        yaml_out_path = Path(args.yaml_out).resolve()
        yaml_out_path.parent.mkdir(parents=True, exist_ok=True)
        using_temp = False
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        yaml_out_path = Path(temp_file.name)
        temp_file.close()
        using_temp = True

    try:
        render_chart_to_yaml(chart_path, yaml_out_path)
        yaml_text = yaml_out_path.read_text()
        images = extract_images_from_yaml(yaml_text)

        if not images:
            logger.info("No image fields found in rendered YAML.")
            return 0

        logger.info(f"Found {len(images)} unique image entries:")
        for img in images:
            logger.info(f"  - {img}")

        any_missing = False
        logger.info("\nChecking images on Docker Hub:")
        for img in images:
            try:
                repository, tag = split_repository_and_tag(img)
            except ValueError as ve:
                logger.info(f"[SKIP] {img} -> {ve}")
                continue

            exists, raw = check_image(repository, tag, args.timeout)
            status = "OK" if exists else "MISSING"
            logger.info(f"[{status}] {repository}:{tag} ({raw})")
            if not exists:
                any_missing = True

        if args.strict and any_missing:
            return 1
        return 0
    finally:
        if using_temp:
            try:
                os.unlink(str(yaml_out_path))
            except Exception:
                pass


if __name__ == "__main__":
    result = main(sys.argv[1:])
    print(f"Process exited with code: {result}")
    sys.exit(result)