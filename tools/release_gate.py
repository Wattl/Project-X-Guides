"""Fail-closed metadata gate for the public Project X guide catalogue.

This validates recorded evidence and exact artifact identities. It does not
execute DCS, assess the quality of a flight test, or grant a release approval.
Only trusted repository maintainers may add or approve catalogue records.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, time, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


REPOSITORY = "Wattl/Project-X-Guides"
GATES = (
    "research", "source_matrix", "glossary", "concept_model", "outline",
    "draft", "dcs_translation", "scenarios", "red_team", "technical_audit",
    "layout", "release_candidate",
)
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
_BUILD = re.compile(r"\d+\.\d+\.\d+\.\d+\Z")
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_FILE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.pdf\Z")
_TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def release_fingerprint(record: dict) -> str:
    """Bind approval to all release fields except the approval object itself."""
    if not isinstance(record, dict):
        raise ValueError("Release must be an object")
    payload = {key: value for key, value in record.items() if key != "approval"}
    try:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("Release is not canonical JSON") from exc
    return hashlib.sha256(raw).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _object(value, name: str) -> dict:
    _require(isinstance(value, dict), f"{name} must be an object")
    return value


def _text(value, name: str, maximum: int = 200) -> str:
    _require(isinstance(value, str) and 0 < len(value) <= maximum
             and value == value.strip() and all(ord(c) >= 32 for c in value),
             f"{name} must be nonempty plain text")
    return value


def _sha(value, name: str) -> str:
    _require(isinstance(value, str) and bool(_SHA.fullmatch(value)),
             f"{name} must be a lowercase SHA-256")
    return value


def _timestamp(value, name: str, now: datetime) -> datetime:
    _text(value, name, 40)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            result = datetime.combine(date.fromisoformat(value), time(), timezone.utc)
        else:
            _require("T" in value, f"{name} must be an ISO date or timestamp")
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            _require(result.tzinfo is not None,
                     f"{name} timestamp must include a timezone")
            result = result.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} is not a valid ISO date/timestamp") from exc
    _require(result <= now, f"{name} is in the future")
    return result


def _report(record: dict, root: Path, artifact_hashes: list[str], build: str) -> None:
    report = _object(record, "verification.report")
    raw_path = _text(report.get("path"), "report.path", 240)
    posix = PurePosixPath(raw_path)
    _require("\\" not in raw_path and not posix.is_absolute()
             and posix.as_posix() == raw_path and len(posix.parts) >= 2
             and posix.parts[0] == "evidence" and ".." not in posix.parts
             and posix.suffix == ".md", "Report must be a Markdown file under evidence/")
    base = root.resolve()
    evidence = (base / "evidence").resolve()
    target = (base / Path(*posix.parts)).resolve()
    _require(evidence.is_relative_to(base) and target.is_relative_to(evidence)
             and target != evidence, "Report path escapes evidence/")
    _require(target.is_file(), "Public test report is missing")
    _require(target.stat().st_size <= 1_000_000, "Public test report is too large")
    raw = target.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == _sha(report.get("sha256"), "report.sha256"),
             "Public test report hash does not match")
    try:
        body = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Public test report must be UTF-8") from exc
    _require(build in body and "Wattl" in body
             and all(value in body for value in artifact_hashes),
             "Public test report must name the tested build, approver and every artifact SHA-256")


def _validate(record: dict, build: str, root: Path, now: datetime) -> tuple[int, int, int]:
    _object(record, "release")
    guide = _text(record.get("guide_id"), "guide_id", 100)
    _require(bool(_SLUG.fullmatch(guide)), "guide_id must be a lowercase slug")
    _text(record.get("title"), "title")
    _text(record.get("module"), "module")
    version = _text(record.get("version"), "version", 40)
    match = _VERSION.fullmatch(version)
    _require(match is not None, "version must contain three numeric components")

    gates = _object(record.get("gates"), "gates")
    _require(all(gates.get(gate) == "passed" for gate in GATES),
             "Required guide workflow gates have not all passed")
    verification = _object(record.get("verification"), "verification")
    _require(verification.get("status") == "passed"
             and verification.get("runtime_tested") is True,
             "A passed practical DCS test is required")
    _require(verification.get("dcs_build") == build,
             "Guide was not tested against the current DCS build")
    tested = _timestamp(verification.get("tested_at"), "tested_at", now)

    rights = _object(record.get("rights"), "rights")
    _require(rights.get("status") == "cleared", "Publication rights are not cleared")
    _text(rights.get("reviewed_by"), "rights.reviewed_by", 100)
    rights_date = _timestamp(rights.get("reviewed_at"), "rights.reviewed_at", now)
    approval = _object(record.get("approval"), "approval")
    _require(approval.get("status") == "approved"
             and approval.get("approved_by") == "Wattl",
             "The repository owner has not approved this release")
    approved = _timestamp(approval.get("approved_at"), "approved_at", now)
    _require(approved >= tested and approved >= rights_date,
             "Approval predates testing or rights review")
    _require(_sha(approval.get("release_fingerprint"), "approval.release_fingerprint")
             == release_fingerprint(record), "Approval does not bind this exact release")

    artifacts = record.get("artifacts")
    _require(isinstance(artifacts, list) and 0 < len(artifacts) <= 32,
             "Release must contain PDF artifacts")
    seen = set()
    hashes = []
    for artifact in artifacts:
        _object(artifact, "artifact")
        filename = _text(artifact.get("filename"), "artifact.filename", 160)
        _require(bool(_FILE.fullmatch(filename)) and ".." not in filename,
                 "Artifact filename must be a safe PDF basename")
        _require(filename.casefold() not in seen, "Duplicate artifact filename")
        seen.add(filename.casefold())
        _text(artifact.get("label"), "artifact.label", 120)
        size = artifact.get("bytes")
        _require(type(size) is int and 0 < size <= 80_000_000,
                 "Artifact size must be between 1 and 80,000,000 bytes")
        hashes.append(_sha(artifact.get("sha256"), "artifact.sha256"))
        url = _text(artifact.get("url"), "artifact.url", 500)
        parsed = urlsplit(url)
        prefix = f"/{REPOSITORY}/releases/download/"
        _require(parsed.scheme == "https" and parsed.netloc == "github.com"
                 and not parsed.query and not parsed.fragment
                 and parsed.path.startswith(prefix),
                 "Artifact URL must be an exact release URL in the public guide repository")
        tail = parsed.path[len(prefix):].split("/")
        _require(len(tail) == 2 and bool(_TAG.fullmatch(tail[0]))
                 and ".." not in tail[0] and tail[1] == filename,
                 "Artifact release tag or filename is invalid")
    _report(verification.get("report"), root, hashes, build)
    return tuple(map(int, match.groups()))


def eligible_releases(catalog: dict, current_dcs_build: str | None,
                      root: Path, now: datetime | None = None) -> tuple[list[dict], list[dict]]:
    """Return latest eligible release per guide plus exclusion reasons.

    A malformed catalogue raises ValueError. A missing or invalid observed DCS
    build excludes every release. Duplicate guide/version identities exclude
    every record with that identity, regardless of which copy looks valid.
    """
    _require(isinstance(catalog, dict) and type(catalog.get("schema_version")) is int
             and catalog["schema_version"] == 1 and isinstance(catalog.get("releases"), list),
             "Catalogue must have schema_version 1 and a releases array")
    now = now or datetime.now(timezone.utc)
    _require(isinstance(now, datetime) and now.tzinfo is not None, "now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    records = catalog["releases"]
    def identity(record):
        if isinstance(record, dict) and isinstance(record.get("guide_id"), str) and isinstance(record.get("version"), str):
            return record["guide_id"], record["version"]
        return None
    counts = Counter(identity(record) for record in records if identity(record) is not None)
    selected = {}
    excluded = []
    for record in records:
        ident = identity(record)
        item = {"id": ident[0] if ident else "unknown", "version": ident[1] if ident else "unknown"}
        try:
            _require(isinstance(current_dcs_build, str) and bool(_BUILD.fullmatch(current_dcs_build)),
                     "Current DCS version is unknown")
            _require(ident is None or counts[ident] == 1, "Duplicate guide/version identity")
            version = _validate(record, current_dcs_build, Path(root), now)
            if ident[0] not in selected or version > selected[ident[0]][0]:
                if ident[0] in selected:
                    previous = selected[ident[0]][1]
                    excluded.append({"id": ident[0], "version": previous["version"], "reason": "Newer eligible release exists"})
                selected[ident[0]] = version, record
            else:
                excluded.append({**item, "reason": "Newer eligible release exists"})
        except (ValueError, OSError, TypeError) as exc:
            excluded.append({**item, "reason": str(exc)})
    return [selected[key][1] for key in sorted(selected)], excluded
