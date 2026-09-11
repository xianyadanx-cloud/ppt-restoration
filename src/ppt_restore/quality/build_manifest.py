"""Build manifest helpers that bind a PPTX to the exact source artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ppt_restore.contracts.schema_v2 import BuildManifest
from ppt_restore.platform.provenance import sha256_file

PathLike = Union[str, Path]


def manifest_path(case_dir: PathLike, pptx_path: PathLike) -> Path:
    """Return the content-addressed manifest path for a PPTX."""

    digest = sha256_file(pptx_path)
    return Path(case_dir) / "builds" / (digest + ".json")


def create_build_manifest(
    case_dir: PathLike,
    output_path: PathLike,
    *,
    canonical_path: PathLike,
    evidence_path: PathLike,
    scene_path: PathLike,
    render_plan_path: PathLike,
    compiler_version: str = "1.0",
    source: str = "scene_v2",
) -> Tuple[BuildManifest, Path]:
    """Hash all inputs and persist one immutable build manifest."""

    output = Path(output_path)
    manifest = BuildManifest(
        schema_version="1.0",
        canonical_sha256=sha256_file(canonical_path),
        evidence_sha256=sha256_file(evidence_path),
        scene_sha256=sha256_file(scene_path),
        render_plan_sha256=sha256_file(render_plan_path),
        pptx_sha256=sha256_file(output),
        compiler_version=str(compiler_version),
        output_path=str(output.resolve()),
        created_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        source=str(source),
    )
    target = Path(case_dir) / "builds" / (manifest.pptx_sha256 + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(manifest.to_json(indent=2) + "\n", encoding="utf-8")
    return manifest, target


def read_build_manifest(path: PathLike) -> BuildManifest:
    return BuildManifest.from_json(Path(path).read_text(encoding="utf-8"))


def validate_build_manifest(
    manifest: BuildManifest,
    *,
    canonical_path: PathLike,
    evidence_path: PathLike,
    scene_path: PathLike,
    render_plan_path: PathLike,
    pptx_path: PathLike,
) -> Dict[str, Any]:
    """Return a machine-readable validation result without mutating files."""

    paths = {
        "canonical_sha256": Path(canonical_path),
        "evidence_sha256": Path(evidence_path),
        "scene_sha256": Path(scene_path),
        "render_plan_sha256": Path(render_plan_path),
        "pptx_sha256": Path(pptx_path),
    }
    mismatches = []
    for field, path in paths.items():
        if not path.is_file():
            mismatches.append("missing %s: %s" % (field, path))
            continue
        actual = sha256_file(path)
        if actual != getattr(manifest, field):
            mismatches.append("%s mismatch" % field)
    output_matches = Path(manifest.output_path).resolve() == Path(pptx_path).resolve()
    if not output_matches:
        mismatches.append("output_path mismatch")
    return {
        "valid": not mismatches,
        "mismatches": mismatches,
        "manifest": manifest.to_dict(),
    }


def find_build_manifest(
    case_dir: PathLike, pptx_path: PathLike
) -> Optional[Tuple[BuildManifest, Path]]:
    """Find the manifest whose filename is the current PPTX hash."""

    pptx = Path(pptx_path)
    if not pptx.is_file():
        return None
    path = manifest_path(case_dir, pptx)
    if not path.is_file():
        return None
    return read_build_manifest(path), path


__all__ = [
    "manifest_path",
    "create_build_manifest",
    "read_build_manifest",
    "validate_build_manifest",
    "find_build_manifest",
]
