#!/usr/bin/env python3

import argparse
import subprocess
import sys
from typing import Iterable, List
from loguru import logger


DEFAULT_SOURCE_NAMESPACE = "bitnami"
DEFAULT_TARGET_NAMESPACE = "infortrend"

# Default images provided by the user
DEFAULT_IMAGES: List[str] = [
    # "bitnami/cassandra:4.0.4-debian-11-r4",
    # "bitnami/cassandra-exporter:2.3.8-debian-11-r4",
    # "bitnami/kafka:3.2.0-debian-11-r3",
    # "bitnami/kubectl:1.24.1-debian-11-r4",
    # "bitnami/kafka-exporter:1.4.2-debian-11-r4",
    # "bitnami/jmx-exporter:0.17.0-debian-11-r4",
    # "bitnami/zookeeper:3.8.0-debian-11-r6",
    # "bitnami/bitnami-shell:11-debian-11-r4",
    # "bitnami/postgresql-repmgr:14.4.0-debian-11-r3",
    # "bitnami/pgpool:4.3.2-debian-11-r9",
    # "bitnami/postgres-exporter:0.10.1-debian-11-r8",
    # "bitnami/bitnami-shell:11-debian-11-r8",
    # "bitnami/redis:6.2.7-debian-11-r3",
    # "bitnami/redis-sentinel:6.2.7-debian-11-r4",
    # "bitnami/redis-exporter:1.40.0-debian-11-r0",
    # "bitnami/redis:7.0.12-debian-11-r2",
    # "bitnami/redis-sentinel:7.0.12-debian-11-r1",
    # "bitnami/redis-exporter:1.51.0-debian-11-r11",
    # "bitnami/os-shell:11-debian-11-r3",
    "bitnami/os-shell:11-debian-11-r90",
]


def _run_command(command: List[str]) -> int:
    process = subprocess.run(command)
    return process.returncode


def _read_images_from_file(path: str) -> List[str]:
    images: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            images.append(line)
    return images


def _normalize_images(images: Iterable[str]) -> List[str]:
    unique = []
    seen = set()
    for image in images:
        item = image.strip()
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _build_target_image_name(image: str, source_ns: str, target_ns: str) -> str:
    prefix = f"{source_ns}/"
    if not image.startswith(prefix):
        raise ValueError(
            f"Image '{image}' does not start with expected source namespace '{prefix}'"
        )
    return image.replace(prefix, f"{target_ns}/", 1)


def pull_and_tag_images(
    images: Iterable[str], source_namespace: str, target_namespace: str, pull_always: bool
) -> int:
    images_list = _normalize_images(images)

    overall_failures = 0

    for image in images_list:
        try:
            target = _build_target_image_name(image, source_namespace, target_namespace)
        except ValueError as e:
            logger.warning(f"[SKIP] {e}")
            overall_failures += 1
            continue

        logger.info(f"=== Processing ===\nSource : {image}\nTarget : {target}")

        if pull_always:
            logger.info(f"[PULL] docker pull {image}")
            rc = _run_command(["docker", "pull", image])
            if rc != 0:
                logger.error(f"[ERROR] Failed to pull {image} (rc={rc}). Skipping tag.")
                overall_failures += 1
                continue
        else:
            logger.info("[SKIP] Pull skipped by flag --no-pull")

        logger.info(f"[TAG] docker tag {image} {target}")
        rc = _run_command(["docker", "tag", image, target])
        if rc != 0:
            logger.error(f"[ERROR] Failed to tag {image} -> {target} (rc={rc})")
            overall_failures += 1
            continue

        logger.info(f"[DONE] {image} -> {target}")

        logger.info(f"[PUSH] docker push {target}")
        rc = _run_command(["docker", "push", target])
        if rc != 0:
            logger.error(f"[ERROR] Failed to push {target} (rc={rc})")
            overall_failures += 1
            continue
    
    for image in images_list:
        try:
            target = _build_target_image_name(image, source_namespace, target_namespace)
        except ValueError as e:
            logger.warning(f"[SKIP] {e}")
            overall_failures += 1
            continue

        logger.info(f"[REMOVE] docker rmi {image}")
        rc = _run_command(["docker", "rmi", image])
        if rc != 0:
            logger.error(f"[ERROR] Failed to remove {image} (rc={rc})")
            overall_failures += 1
            continue

        logger.info(f"[REMOVE] docker rmi {target}")
        rc = _run_command(["docker", "rmi", target])
        if rc != 0:
            logger.error(f"[ERROR] Failed to remove {target} (rc={rc})")
            overall_failures += 1
            continue

        logger.info(f"[DONE] Removed {image} and {target}")
        

    return overall_failures


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pull Docker images and retag them by replacing the source namespace with the "
            "target namespace."
        )
    )
    parser.add_argument(
        "--source-namespace",
        default=DEFAULT_SOURCE_NAMESPACE,
        help=f"Source namespace prefix (default: '{DEFAULT_SOURCE_NAMESPACE}')",
    )
    parser.add_argument(
        "--target-namespace",
        default=DEFAULT_TARGET_NAMESPACE,
        help=f"Target namespace prefix (default: '{DEFAULT_TARGET_NAMESPACE}')",
    )
    parser.add_argument(
        "--images-file",
        default=None,
        help=(
            "Path to a file containing images (one per line). If not provided, a built-in "
            "default list will be used."
        ),
    )
    parser.add_argument(
        "--no-pull",
        action="store_true",
        help="Do not pull images before tagging (tag only).",
    )

    args = parser.parse_args(argv)

    if args.images_file:
        images = _read_images_from_file(args.images_file)
    else:
        images = list(DEFAULT_IMAGES)

    failures = pull_and_tag_images(
        images=images,
        source_namespace=args.source_namespace,
        target_namespace=args.target_namespace,
        pull_always=not args.no_pull,
    )

    if failures:
        logger.error(f"\nCompleted with {failures} errors.")
        return 1

    logger.info("All images processed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:])) 