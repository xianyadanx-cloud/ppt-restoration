"""Case directory and stable JSON artifact I/O."""

import hashlib
import json
from pathlib import Path
from typing import Any, Union

from ppt_restore.contracts.models import CaseManifest, Registration
from ppt_restore.contracts.schema_v2 import SceneSpecV2

PathLike = Union[str, Path]


def sha256_file(path: PathLike, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while True:
            data = stream.read(chunk_size)
            if not data:
                break
            digest.update(data)
    return digest.hexdigest()


def write_json(path: PathLike, value: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def read_json(path: PathLike) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_case_dir(case_dir: PathLike) -> Path:
    root = Path(case_dir)
    root.mkdir(parents=True, exist_ok=True)
    for name in ("source", "renders", "reports", "candidates"):
        (root / name).mkdir(exist_ok=True)
    return root


def write_case_manifest(case_dir: PathLike, manifest: CaseManifest) -> Path:
    return write_json(Path(case_dir) / "case.json", manifest)


def read_case_manifest(case_dir: PathLike) -> CaseManifest:
    return CaseManifest.from_dict(read_json(Path(case_dir) / "case.json"))


def write_registration(case_dir: PathLike, registration: Registration) -> Path:
    return write_json(Path(case_dir) / "registration.json", registration)


def read_registration(case_dir: PathLike) -> Registration:
    return Registration.from_dict(read_json(Path(case_dir) / "registration.json"))


def read_scene_any(case_dir: PathLike) -> SceneSpecV2:
    """Read the supported semantic scene, rejecting obsolete formats."""
    data = read_json(Path(case_dir) / "scene.json")
    if str(data.get("schema_version", "")) != "2.0":
        raise ValueError(
            "Only SceneSpec v2 is supported; prepare and ingest a new case"
        )
    return SceneSpecV2.from_dict(data)
