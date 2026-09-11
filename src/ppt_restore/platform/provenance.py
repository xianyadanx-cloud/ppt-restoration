"""Reproducibility and provenance helpers used by render and verification runs."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

PathLike = Union[os.PathLike, str]


def sha256_file(path: PathLike, chunk_size: int = 1024 * 1024) -> str:
    """Return a stable SHA-256 for a file.

    A missing or unreadable file raises the normal ``OSError`` so callers do
    not accidentally record a successful run with a fake hash.
    """

    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@lru_cache(maxsize=16)
def _command_version(command: str) -> Optional[str]:
    try:
        proc = subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=4,
            check=False,
        )
        text = (proc.stdout or "").strip()
        return text.splitlines()[0][:300] if text else None
    except (OSError, subprocess.SubprocessError):
        return None


def environment_info(
    *,
    renderer: Optional[str] = None,
    renderer_version: Optional[str] = None,
    fonts: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Collect only deterministic, useful environment facts for a report."""

    result: Dict[str, Any] = {
        "os": platform.platform(),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "machine": platform.machine(),
    }
    if renderer:
        result["renderer"] = renderer
    if renderer_version:
        result["renderer_version"] = renderer_version
    else:
        result["renderer_version"] = None
    if fonts is not None:
        result["fonts"] = dict(fonts)
    # Useful when a caller does not yet have a backend-specific version.
    result["available_commands"] = {
        name: _command_version(name) for name in ("soffice", "libreoffice", "pdftoppm")
    }
    return result


@dataclass(frozen=True)
class ProvenanceRecord:
    schema_version: str = "1.0"
    input_sha256: Optional[str] = None
    pptx_sha256: Optional[str] = None
    scene_sha256: Optional[str] = None
    renderer: Optional[str] = None
    renderer_version: Optional[str] = None
    os: Optional[str] = None
    python: Optional[str] = None
    fonts: Optional[Dict[str, Any]] = None
    icc_profile: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_provenance(
    *,
    input_path: Optional[PathLike] = None,
    pptx_path: Optional[PathLike] = None,
    scene_path: Optional[PathLike] = None,
    renderer: Optional[str] = None,
    renderer_version: Optional[str] = None,
    fonts: Optional[Mapping[str, Any]] = None,
    icc_profile: Optional[str] = None,
) -> ProvenanceRecord:
    """Build a provenance record without mutating any files."""

    env = environment_info(
        renderer=renderer, renderer_version=renderer_version, fonts=fonts
    )
    return ProvenanceRecord(
        input_sha256=sha256_file(input_path) if input_path else None,
        pptx_sha256=sha256_file(pptx_path) if pptx_path else None,
        scene_sha256=sha256_file(scene_path) if scene_path else None,
        renderer=renderer,
        renderer_version=renderer_version,
        os=env["os"],
        python=env["python"],
        fonts=dict(fonts) if fonts is not None else None,
        icc_profile=icc_profile,
    )


def write_json(path: PathLike, payload: Mapping[str, Any]) -> Path:
    """Write a UTF-8, stable JSON artifact, creating only its parent directory."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def runtime_summary() -> Dict[str, Any]:
    """Small helper for ``doctor`` and case manifests."""

    return environment_info()
