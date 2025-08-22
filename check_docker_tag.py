#!/usr/bin/env python3

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, List


DOCKER_AUTH_URL = "https://auth.docker.io/token"
DOCKER_REGISTRY_URL = "https://registry-1.docker.io"


def _normalize_repository_name(repository: str) -> str:
    repository = repository.strip()
    if "/" not in repository:
        return f"library/{repository}"
    return repository


def _fetch_bearer_token(repository: str, timeout: int = 15) -> Optional[str]:
    query = urllib.parse.urlencode(
        {
            "service": "registry.docker.io",
            "scope": f"repository:{repository}:pull",
        }
    )
    url = f"{DOCKER_AUTH_URL}?{query}"
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("token")
    except urllib.error.HTTPError as http_err:
        print(f"[ERROR] Failed to get token for {repository}: HTTP {http_err.code}")
    except urllib.error.URLError as url_err:
        print(f"[ERROR] Failed to get token for {repository}: {url_err}")
    except Exception as exc:
        print(f"[ERROR] Failed to get token for {repository}: {exc}")
    return None


def docker_hub_tag_exists(repository: str, tag: str, timeout: int = 15) -> bool:
    normalized_repo = _normalize_repository_name(repository)
    token = _fetch_bearer_token(normalized_repo, timeout=timeout)
    if not token:
        return False

    manifest_url = f"{DOCKER_REGISTRY_URL}/v2/{normalized_repo}/manifests/{tag}"
    request = urllib.request.Request(manifest_url)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header(
        "Accept",
        ", ".join(
            [
                "application/vnd.docker.distribution.manifest.v2+json",
                "application/vnd.docker.distribution.manifest.list.v2+json",
                "application/vnd.oci.image.index.v1+json",
                "application/vnd.oci.image.manifest.v1+json",
            ]
        ),
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as http_err:
        if http_err.code == 404:
            return False
        print(
            f"[ERROR] Manifest query failed for {repository}:{tag} - HTTP {http_err.code}"
        )
        return False
    except urllib.error.URLError as url_err:
        print(f"[ERROR] Manifest query failed for {repository}:{tag} - {url_err}")
        return False
    except Exception as exc:
        print(f"[ERROR] Manifest query failed for {repository}:{tag} - {exc}")
        return False


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check if a Docker Hub image:tag exists via the Docker Registry v2 API."
    )
    parser.add_argument("repository", help="Repository name, e.g. bitnami/os-shell")
    parser.add_argument("tag", help="Tag name, e.g. 11-debian-11-r90")
    parser.add_argument(
        "--timeout", type=int, default=15, help="HTTP timeout in seconds (default: 15)"
    )
    args = parser.parse_args(argv)

    exists = docker_hub_tag_exists(args.repository, args.tag, timeout=args.timeout)
    print("exists" if exists else "missing")
    return 0 if exists else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:])) 