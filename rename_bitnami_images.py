#!/usr/bin/env python3

import argparse
import os
import sys
from typing import List, Tuple


def replace_namespace_in_line(line: str, source_ns: str, target_ns: str) -> Tuple[str, bool]:
    source_prefix = f"{source_ns}/"
    target_prefix = f"{target_ns}/"

    if source_prefix not in line:
        return line, False

    new_line = line.replace(source_prefix, target_prefix)
    return new_line, True


def process_values_file(filepath: str, source_ns: str, target_ns: str) -> Tuple[int, int]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return 0, 0

    changed = False
    replacements = 0
    new_lines: List[str] = []

    for line in lines:
        new_line, did_replace = replace_namespace_in_line(line, source_ns, target_ns)
        if did_replace:
            changed = True
            replacements += 1
        new_lines.append(new_line)

    if changed:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            return 0, 0

    return (1 if changed else 0), replacements


def update_chart_version(chart_dir: str) -> None:
    chart_yaml_path = os.path.join(chart_dir, "Chart.yaml")
    if os.path.isfile(chart_yaml_path):
        with open(chart_yaml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith("version:"):
                current_version = line.split()[1]
                prefix = current_version.split('+')[0]
                suffix = '+'.join(current_version.split('+')[1:])
                new_prefix = '.'.join(prefix.split('.')[:-1] + [str(int(prefix.split('.')[-1]) + 1)])
                new_version = f"{new_prefix}+{suffix}" if suffix else new_prefix
                lines[i] = f"version: {new_version}\n"
                break

        with open(chart_yaml_path, "w", encoding="utf-8") as f:
            f.writelines(lines)


def update_changelog(chart_dir: str, current_version: str) -> None:
    changelog_path = os.path.join(chart_dir, "CHANGELOG.md")
    if os.path.isfile(changelog_path):
        with open(changelog_path, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0, 0)
            # Find the position to insert after "# Change Log"
            insert_position = content.find("# Change Log")
            if insert_position != -1:
                insert_position += len("# Change Log\n")
                changelog_entry = (
                    f"## {current_version}\n"
                    "### Modified\n"
                    "1. values.yaml: Update default `image.repository` to `bitnamilegacy`.\n\n"
                )
                # Insert the changelog entry after "# Change Log"
                updated_content = content[:insert_position] + changelog_entry + content[insert_position:]
                f.write(updated_content)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan values.yaml under a path, and replace 'bitnami/' with a target namespace prefix (default 'bitnamilegacy/')."
        )
    )
    parser.add_argument("path", help="Root path to scan (file or directory)")
    parser.add_argument(
        "--source-namespace",
        default="bitnami",
        help="Source namespace to replace (default: bitnami)",
    )
    parser.add_argument(
        "--target-namespace",
        default="bitnamilegacy",
        help="Target namespace to use (default: bitnamilegacy)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files",
    )

    args = parser.parse_args(argv)

    values_file_path = os.path.join(args.path, "values.yaml")
    if not os.path.exists(values_file_path):
        print(f"[ERROR] values.yaml does not exist in the specified path: {args.path}")
        return 1

    if args.dry_run:
        try:
            with open(values_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as exc:
            print(f"[ERROR] Cannot read file: {values_file_path} ({exc})")
            return 1
        reps = 0
        for line in lines:
            _, did_replace = replace_namespace_in_line(line, args.source_namespace, args.target_namespace)
            if did_replace:
                reps += 1
        print(f"[DRY] {values_file_path} -> {reps} replacement(s)")
        return 0

    changed, reps = process_values_file(values_file_path, args.source_namespace, args.target_namespace)
    if changed:
        update_chart_version(args.path)
        chart_yaml_path = os.path.join(args.path, "Chart.yaml")
        with open(chart_yaml_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("version:"):
                    current_version = line.split()[1]
                    break
        update_changelog(args.path, current_version)
        print(f"[EDIT] {values_file_path} -> {reps} replacement(s)")
    else:
        print(f"[SKIP] {values_file_path} (no changes)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:])) 