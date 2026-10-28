#!/usr/bin/env python3
"""Stage-based renderer for AI Coach Daily Demo fixed-30-scene projects."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
REMOTION_DIR = SKILL_DIR / "remotion"
PUBLIC_ROOT = REMOTION_DIR / "public" / "ai-coach-daily-demo"
CONFIG_ENV = Path.home() / ".config" / "ai-coach-daily-demo" / ".env"
DEFAULT_LOGO_IMAGE = SKILL_DIR / "assets" / "default-logo.jpg"
AI_LAB_ROOT = Path("/Users/henry/Desktop/财叔 AI Lab")
MIAODONG_ROOT = Path("/Users/henry/Desktop/秒懂金融学院")
CAISHU_PROJECT_ROOT = AI_LAB_ROOT / "03_内容生产" / "项目"
MIAODONG_AI_FINANCE_ROOT = (
    MIAODONG_ROOT / "02_内容生产" / "视频" / "每天一个AI理财小技巧"
)
ARCHIVABLE_PROJECT_ROOTS = (
    CAISHU_PROJECT_ROOT,
    MIAODONG_AI_FINANCE_ROOT,
)
COMMON_ASSET_ROOT = AI_LAB_ROOT / "03_内容生产" / "共享素材"
DEFAULT_CORNER_LOGO_IMAGE = (
    MIAODONG_ROOT / "00_品牌与业务中枢" / "品牌资产" / "logo" / "miaodong_finance_logo.png"
)
DEFAULT_CAISHU_CORNER_LOGO_IMAGE = (
    AI_LAB_ROOT / "00_品牌与经营" / "品牌资产" / "logo" / "caishu_ai_lab_primary_logo.png"
)
DEFAULT_BGM_PATH = (
    COMMON_ASSET_ROOT / "音频" / "赛文乔伊_一个人一张画布_BGM去人声_修复版_v2.mp3"
)
CREATION_ARCHIVE_HOOK = Path(
    "/Users/henry/.shared/skills/creation-knowledge-manager/scripts/archive_hook.py"
)
FPS = 30
SCHEMA_VERSION = 1
ALLOWED_IMAGE_SOURCE_TYPES = {
    "ai_generated",
    "user_screenshot",
    "recording_frame",
    "approved_ai_coach_asset",
}
FORBIDDEN_IMAGE_SOURCE_TYPES = {
    "wechat_article_cover",
    "wechat_article_body",
    "public_account_cover",
    "public_account_article_image",
}
FORBIDDEN_EDITORIAL_PATH_PARTS = {
    "article_publish_assets",
    "wechat_article_assets",
    "公众号文章配图",
    "公众号封面",
}

sys.path.insert(0, str(SCRIPTS_DIR))
from ai_coach_demo_builder import (  # noqa: E402
    SERIES_TITLE,
    expected_scene_ids,
    output_dir_for_topic,
    parse_script_file,
    public_slug,
    script_fingerprint,
    sha256_file,
    sha256_text,
    write_json,
)
from brand_profiles import PROFILES, apply_brand_defaults, resolve_brand_profile


@dataclass
class AudioMeta:
    path: Path
    duration_ms: int
    provider: str
    model: str
    voice: str
    speed: float


def load_env_file(path: Path = CONFIG_ENV) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def run(command: List[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or f"command failed: {' '.join(command)}")
    return result


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(project_dir: Path, raw: str | Path) -> Path:
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = project_dir / path
    return path.resolve()


def ffprobe(path: Path) -> Dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(result.stdout)


def ffprobe_duration_seconds(path: Path) -> float:
    try:
        probe = ffprobe(path)
        return float((probe.get("format") or {}).get("duration") or 0.0)
    except Exception:
        return 0.0


def ffprobe_dimensions(path: Path) -> Tuple[int, int]:
    probe = ffprobe(path)
    stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), {})
    return int(stream.get("width") or 0), int(stream.get("height") or 0)


def probe_audio_duration_ms(path: Path) -> int:
    seconds = ffprobe_duration_seconds(path)
    return int(seconds * 1000) if seconds > 0 else 0


def scene_index(scene_id: str) -> int:
    return int(scene_id.split("_", 1)[1])


def validate_script(project_dir: Path, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    script_path = resolve_path(project_dir, plan.get("script_path", "口播文案.txt"))
    resolved_project = project_dir.expanduser().resolve()
    if resolved_project.name == "03_制作" and resolved_project.parent.name == "视频":
        narration_root = (resolved_project.parent / "01_口播").resolve()
        try:
            script_path.resolve().relative_to(narration_root)
        except ValueError as exc:
            raise ValueError(
                f"标准财叔视频的 script_path 必须位于 {narration_root}"
            ) from exc
        if not re.fullmatch(r"口播文案-v\d{2,}\.txt", script_path.name):
            raise ValueError("标准财叔视频口播必须使用 口播文案-vNN.txt 版本命名")
    scene_count = int(plan.get("scene_count") or 30)
    scenes = parse_script_file(script_path, strict=True, expected_count=scene_count)
    plan_ids = [scene.get("id") for scene in plan.get("scenes", [])]
    if plan_ids != expected_scene_ids(scene_count):
        raise ValueError(
            f"scene_plan.json must contain exactly scene_01 through scene_{scene_count:02d}"
        )
    by_id = {scene["id"]: scene for scene in scenes}
    for scene in plan["scenes"]:
        scene_id = scene["id"]
        narration = by_id[scene_id]["narration"]
        if scene.get("narration") and scene["narration"] != narration:
            raise ValueError(f"{scene_id} narration differs from 口播文案.txt")
        scene["narration"] = narration
        scene.setdefault("caption", by_id[scene_id]["caption"])
    return scenes


def load_plan(project_dir: Path) -> Dict[str, Any]:
    plan_path = project_dir / "scene_plan.json"
    if not plan_path.exists():
        raise FileNotFoundError(f"missing scene_plan.json: {plan_path}")
    plan = read_json(plan_path)
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported scene_plan schema_version: {plan.get('schema_version')}")
    validate_script(project_dir, plan)
    return plan


def built_in_corner_logo_variants() -> Dict[str, Dict[str, Any]]:
    return {
        name: copy.deepcopy(profile['corner_logo'])
        for name, profile in PROFILES.items()
    }


def corner_logo_variant_configs(plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    variants = built_in_corner_logo_variants()
    raw = plan.get("corner_logo_variants") or {}
    items = raw.get("items") if isinstance(raw, dict) else None
    if isinstance(items, dict):
        for key, value in items.items():
            if isinstance(value, dict) and value.get("path"):
                variant = str(key)
                variants[variant] = {
                    "variant": value.get("variant") or variant,
                    "path": value["path"],
                    "series_title": value.get("series_title"),
                    "width": int(value.get("width") or 136),
                    "height": int(value.get("height") or 136),
                    "background": value.get("background"),
                    "padding_x": int(value.get("padding_x") or 0),
                    "padding_y": int(value.get("padding_y") or 0),
                    "border_radius": int(value.get("border_radius") or 0),
                }
    return variants


def default_corner_logo_variant_ids(plan: Dict[str, Any]) -> List[str]:
    render_variants = plan.get("render_variants") or {}
    ids = render_variants.get("logo_variants") if isinstance(render_variants, dict) else None
    if ids:
        return [str(item) for item in ids]
    raw = plan.get("corner_logo_variants") or {}
    default_ids = raw.get("default") if isinstance(raw, dict) else None
    return [str(item) for item in default_ids] if default_ids else []


def apply_corner_logo_variant(plan: Dict[str, Any], variant_id: Optional[str]) -> Dict[str, Any]:
    if not variant_id:
        return plan
    variants = corner_logo_variant_configs(plan)
    if variant_id not in variants:
        raise ValueError(
            f"unknown corner logo variant {variant_id!r}; available: {sorted(variants)}"
        )
    plan = copy.deepcopy(plan)
    config = variants[variant_id]
    if variant_id in PROFILES:
        plan['brand_profile'] = variant_id
    if config.get("series_title"):
        plan["series_title"] = str(config["series_title"])
    plan["corner_logo"] = {
        "variant": str(config.get("variant") or variant_id),
        "path": config["path"],
        "width": int(config.get("width") or 136),
        "height": int(config.get("height") or 136),
        "background": config.get("background"),
        "padding_x": int(config.get("padding_x") or 0),
        "padding_y": int(config.get("padding_y") or 0),
        "border_radius": int(config.get("border_radius") or 0),
    }
    plan["_render_variant"] = {"kind": "corner_logo", "id": variant_id}
    return plan


def source_recordings_by_id(project_dir: Path, plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in plan.get("source_recordings", []):
        source_id = str(item.get("id") or "")
        if not source_id:
            raise ValueError("source_recordings item missing id")
        path = resolve_path(project_dir, item["path"])
        if not path.exists():
            raise FileNotFoundError(f"source recording missing: {path}")
        if item.get("sha256") and item["sha256"] != sha256_file(path):
            raise ValueError(f"{source_id} source recording hash changed")
        result[source_id] = {**item, "path": str(path)}
    return result


def approval_hash(project_dir: Path, item: Dict[str, Any]) -> str:
    approval = item.get("approval") or {}
    if approval.get("status") != "approved":
        raise ValueError("final image is not approved")
    path = resolve_path(project_dir, item["path"])
    actual = sha256_file(path)
    if approval.get("sha256") != actual:
        raise ValueError(f"approved image hash changed: {path}")
    return actual


def visual_paths_for_hash(project_dir: Path, scene: Dict[str, Any]) -> List[Path]:
    visual = scene.get("visual") or {}
    kind = visual.get("kind")
    if kind == "image":
        return [resolve_path(project_dir, visual["path"])]
    if kind == "sequence":
        return [resolve_path(project_dir, item["path"]) for item in visual.get("items", [])]
    if kind == "video":
        path = visual.get("path")
        return [resolve_path(project_dir, path)] if path else []
    return []


def validate_image_source(
    project_dir: Path,
    item: Dict[str, Any],
    *,
    scene_id: str,
    require_source_type: bool,
) -> None:
    source_type = str(item.get("source_type") or "").strip()
    if source_type in FORBIDDEN_IMAGE_SOURCE_TYPES:
        raise ValueError(
            f"{scene_id} uses forbidden editorial source_type={source_type}; "
            "AI Coach scenes may use only real screenshots/recordings, newly generated "
            "AI Coach illustrations, or approved AI Coach assets"
        )
    if source_type and source_type not in ALLOWED_IMAGE_SOURCE_TYPES:
        raise ValueError(f"{scene_id} has unknown image source_type={source_type}")
    if require_source_type and not source_type:
        raise ValueError(
            f"{scene_id} missing visual.source_type under material_policy_version=1"
        )

    path = resolve_path(project_dir, item["path"])
    path_text = str(path).casefold()
    matched = next(
        (fragment for fragment in FORBIDDEN_EDITORIAL_PATH_PARTS if fragment.casefold() in path_text),
        None,
    )
    if matched:
        raise ValueError(
            f"{scene_id} image path comes from forbidden public-account editorial assets "
            f"({matched}): {path}"
        )


def validate_visuals(project_dir: Path, plan: Dict[str, Any], *, allow_unapproved: bool = False) -> None:
    sources = source_recordings_by_id(project_dir, plan)
    scenes = plan["scenes"]
    seen_hashes: Dict[str, str] = {}
    scene_ids = {scene["id"] for scene in scenes}
    require_source_type = int(plan.get("material_policy_version") or 0) >= 1

    for scene in scenes:
        scene_id = scene["id"]
        visual = scene.get("visual")
        if not isinstance(visual, dict) or not visual.get("kind"):
            raise ValueError(f"{scene_id} missing visual.kind")
        kind = visual["kind"]
        if scene.get("layout") not in {"illustration", "recording"}:
            raise ValueError(f"{scene_id} layout must be illustration or recording")

        if kind == "reuse":
            reuse_of = visual.get("reuse_of")
            if reuse_of not in scene_ids:
                raise ValueError(f"{scene_id} reuse_of unknown: {reuse_of}")
            if reuse_of >= scene_id:
                raise ValueError(f"{scene_id} reuse_of must point to an earlier scene")
            continue

        if kind == "image":
            validate_image_source(
                project_dir,
                visual,
                scene_id=scene_id,
                require_source_type=require_source_type,
            )
            path = resolve_path(project_dir, visual["path"])
            if not path.exists():
                raise FileNotFoundError(f"{scene_id} image missing: {path}")
            if not allow_unapproved:
                digest = approval_hash(project_dir, visual)
                prior = seen_hashes.get(digest)
                if prior:
                    raise ValueError(f"{scene_id} accidentally reuses image from {prior}; use reuse_of")
                seen_hashes[digest] = scene_id
        elif kind == "sequence":
            items = visual.get("items") or []
            if not items:
                raise ValueError(f"{scene_id} sequence has no items")
            for item in items:
                validate_image_source(
                    project_dir,
                    item,
                    scene_id=scene_id,
                    require_source_type=require_source_type,
                )
                path = resolve_path(project_dir, item["path"])
                if not path.exists():
                    raise FileNotFoundError(f"{scene_id} sequence item missing: {path}")
                if not allow_unapproved:
                    approval_hash(project_dir, item)
        elif kind == "video":
            if scene["layout"] != "recording":
                raise ValueError(f"{scene_id} video visual must use recording layout")
            source_id = visual.get("source_id")
            if source_id and source_id not in sources:
                raise ValueError(f"{scene_id} unknown source_id: {source_id}")
            if visual.get("path") and not resolve_path(project_dir, visual["path"]).exists():
                raise FileNotFoundError(f"{scene_id} video clip missing: {visual['path']}")
            if not visual.get("path") and not (source_id and "in_sec" in visual and "out_sec" in visual):
                raise ValueError(f"{scene_id} video requires path or source_id/in_sec/out_sec")
            for key in ("semantic_event", "required_evidence", "risk"):
                if not visual.get(key):
                    raise ValueError(f"{scene_id} recording visual missing {key}")
        else:
            raise ValueError(f"{scene_id} unsupported visual.kind: {kind}")

    # Validate explicit reuse and catch accidental rendered-asset reuse after resolving reuse scenes.
    resolved_hashes: Dict[str, str] = {}
    for scene in scenes:
        visual = scene["visual"]
        scene_id = scene["id"]
        if visual["kind"] == "reuse":
            resolved_hashes[scene_id] = resolved_hashes[str(visual["reuse_of"])]
            continue
        hashes = [sha256_file(path) for path in visual_paths_for_hash(project_dir, scene) if path.exists()]
        if hashes:
            digest = sha256_text("|".join(hashes))
            prior = next((sid for sid, old in resolved_hashes.items() if old == digest), None)
            if prior and scene_id not in {s["id"] for s in scenes if (s.get("visual") or {}).get("reuse_of") == prior}:
                raise ValueError(f"{scene_id} reuses visual from {prior} without reuse_of")
            resolved_hashes[scene_id] = digest


def validate_continuity(plan: Dict[str, Any]) -> None:
    group_positions: Dict[str, List[int]] = {}
    for position, scene in enumerate(plan["scenes"]):
        visual = scene.get("visual") or {}
        group = visual.get("continuity_group")
        strict = bool(visual.get("strict_continuity")) or str(group or "").startswith(("pdf_", "deliverable_"))
        if group and strict:
            group_positions.setdefault(str(group), []).append(position)
    for group, positions in group_positions.items():
        if len(positions) <= 1:
            continue
        expected = list(range(min(positions), max(positions) + 1))
        if positions != expected:
            raise ValueError(f"continuity group {group} is interrupted by non-group scenes")


def validate_narration_groups(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_groups = plan.get("narration_groups") or []
    if not raw_groups:
        return []
    expected_ids = [scene["id"] for scene in plan["scenes"]]
    positions = {scene_id: index for index, scene_id in enumerate(expected_ids)}
    normalized: List[Dict[str, Any]] = []
    flattened: List[str] = []
    seen_group_ids: set[str] = set()
    for index, raw in enumerate(raw_groups, 1):
        group_id = str(raw.get("id") or f"group_{index:02d}").strip()
        if not group_id or group_id in seen_group_ids:
            raise ValueError(f"duplicate or empty narration group id: {group_id!r}")
        seen_group_ids.add(group_id)
        scene_ids = [str(scene_id) for scene_id in (raw.get("scenes") or [])]
        if not scene_ids:
            raise ValueError(f"narration group {group_id} has no scenes")
        if any(scene_id not in positions for scene_id in scene_ids):
            unknown = [scene_id for scene_id in scene_ids if scene_id not in positions]
            raise ValueError(f"narration group {group_id} has unknown scenes: {unknown}")
        scene_positions = [positions[scene_id] for scene_id in scene_ids]
        if scene_positions != list(range(min(scene_positions), max(scene_positions) + 1)):
            raise ValueError(f"narration group {group_id} scenes must be contiguous")
        flattened.extend(scene_ids)
        normalized.append({"id": group_id, "scenes": scene_ids})
    if flattened != expected_ids:
        raise ValueError(
            "narration_groups must cover scene_01 through scene_30 exactly once and in order"
        )
    return normalized


def validate_plan(project_dir: Path, *, allow_unapproved: bool = False) -> Dict[str, Any]:
    plan = load_plan(project_dir)
    validate_visuals(project_dir, plan, allow_unapproved=allow_unapproved)
    validate_continuity(plan)
    validate_narration_groups(plan)
    return plan


def decode_audio_payload(payload: str) -> bytes:
    raw = (payload or "").strip()
    if not raw:
        return b""
    if raw.startswith(("http://", "https://")):
        with urllib.request.urlopen(raw, timeout=60) as response:
            return response.read()
    # MiniMax currently returns audio as a hexadecimal string. Hex characters
    # are also valid Base64 characters, so trying Base64 first silently
    # produces corrupt audio instead of raising an error.
    if re.fullmatch(r"[0-9A-Fa-f]+", raw) and len(raw) % 2 == 0:
        return bytes.fromhex(raw)
    try:
        return base64.b64decode(raw, validate=True)
    except Exception:
        padding = "=" * (-len(raw) % 4)
        return base64.b64decode(raw + padding)


def tts_settings(speed: float, provider: str) -> Dict[str, Any]:
    timing_mode = (os.getenv("AI_COACH_TTS_TIMING_MODE") or "natural").strip().lower()
    if timing_mode not in {"natural", "diagnostic"}:
        raise ValueError(
            f"AI_COACH_TTS_TIMING_MODE must be natural or diagnostic, got {timing_mode!r}"
        )
    diagnostic = timing_mode == "diagnostic"
    return {
        "provider": provider,
        "model": os.getenv("MINIMAX_TTS_MODEL") or "speech-2.8-turbo",
        "voice": os.getenv("AI_COACH_VOICE_ID") or os.getenv("MINIMAX_VOICE_ID") or "laoliang_story_clone_20260313",
        "speed": round(speed, 3),
        "timing_mode": timing_mode,
        "edge_trim_ms": (
            max(0, int(os.getenv("AI_COACH_TTS_EDGE_TRIM_MS", "0"))) if diagnostic else 0
        ),
        "max_pause_ms": (
            max(0, int(os.getenv("AI_COACH_TTS_MAX_PAUSE_MS", "0"))) if diagnostic else 0
        ),
    }


def audio_cache_payload(text: str, speed: float, provider: str) -> Dict[str, Any]:
    return {"schema": 4, "text": text, **tts_settings(speed, provider)}


def audio_duration_frames(duration_ms: int, *, fps: int = FPS) -> int:
    """Use the untouched source audio as the exact scene timeline."""
    return max(1, int(math.ceil(max(0, duration_ms) / 1000.0 * fps)))


def audio_timing_settings() -> Dict[str, Any]:
    settings = tts_settings(
        float(os.getenv("AI_COACH_TTS_SPEED") or "1.13"),
        "minimax",
    )
    return {
        "timing_mode": settings["timing_mode"],
        "edge_trim_ms": settings["edge_trim_ms"],
        "max_pause_ms": settings["max_pause_ms"],
        "timeline_policy": "source_audio_exact",
        "scene_tail_frames": 0,
        "recording_tail_frames": 0,
        "image_min_seconds": 0.0,
        "recording_min_seconds": 0.0,
    }


def trim_audio_edges(path: Path, *, keep_ms: int) -> None:
    if keep_ms <= 0:
        return
    keep_seconds = keep_ms / 1000.0
    output = path.with_name(f"{path.stem}.edge-trim{path.suffix}")
    edge_filter = (
        "silenceremove="
        "start_periods=1:start_duration=0.05:start_threshold=-42dB:"
        f"start_silence={keep_seconds:.3f}"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-af",
            f"{edge_filter},areverse,{edge_filter},areverse",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(output),
        ]
    )
    os.replace(output, path)


def compress_audio_pauses(path: Path, *, max_pause_ms: int) -> None:
    if max_pause_ms <= 0:
        return
    max_pause = max_pause_ms / 1000.0
    result = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            f"silencedetect=noise=-42dB:d={max_pause:.3f}",
            "-f",
            "null",
            "-",
        ]
    )
    starts = [float(value) for value in re.findall(r"silence_start:\s*([0-9.]+)", result.stderr)]
    ends = [
        (float(end), float(duration))
        for end, duration in re.findall(
            r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)",
            result.stderr,
        )
    ]
    silences = [
        (start, end)
        for start, (end, duration) in zip(starts, ends)
        if duration > max_pause + 0.02
    ]
    if not silences:
        return
    total_duration = ffprobe_duration_seconds(path)
    removals: List[Tuple[float, float]] = []
    for start, end in silences:
        excess = (end - start) - max_pause
        if excess <= 0.02:
            continue
        midpoint = (start + end) / 2.0
        removals.append((midpoint - excess / 2.0, midpoint + excess / 2.0))
    if not removals:
        return
    keep_ranges: List[Tuple[float, float]] = []
    cursor = 0.0
    for start, end in removals:
        if start > cursor:
            keep_ranges.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < total_duration:
        keep_ranges.append((cursor, total_duration))
    if not keep_ranges:
        return
    filters = []
    labels = []
    for index, (start, end) in enumerate(keep_ranges):
        label = f"a{index}"
        filters.append(
            f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[outa]")
    output = path.with_name(f"{path.stem}.pause-trim{path.suffix}")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outa]",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(output),
        ]
    )
    os.replace(output, path)


def normalize_audio_timing(path: Path, settings: Dict[str, Any]) -> None:
    trim_audio_edges(path, keep_ms=int(settings["edge_trim_ms"]))
    compress_audio_pauses(path, max_pause_ms=int(settings["max_pause_ms"]))


def minimax_synthesize(text: str, output_path: Path, *, speed: float) -> AudioMeta:
    api_key = (os.getenv("MINIMAX_API_KEY") or "").strip()
    group_id = (os.getenv("MINIMAX_GROUP_ID") or "").strip()
    if not api_key or not group_id:
        raise RuntimeError("MiniMax TTS is not configured")
    settings = tts_settings(speed, "minimax")
    payload = {
        "text": text,
        "voice_setting": {
            "voice_id": settings["voice"],
            "speed": max(0.5, min(2.0, speed)),
            "vol": float(os.getenv("AI_COACH_TTS_VOLUME", "1.08")),
            "pitch": int(os.getenv("AI_COACH_TTS_PITCH", "0")),
        },
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
        "language": "zh-CN",
        "model": settings["model"],
    }
    request = urllib.request.Request(
        f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=80) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode("utf-8", errors="ignore")) from exc
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code") != 0:
        raise RuntimeError(base_resp.get("status_msg") or "MiniMax TTS failed")
    audio_bytes = decode_audio_payload(data.get("data", {}).get("audio", ""))
    if not audio_bytes:
        raise RuntimeError("MiniMax returned empty audio")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_bytes)
    if settings["timing_mode"] == "diagnostic":
        normalize_audio_timing(output_path, settings)
    duration_ms = probe_audio_duration_ms(output_path)
    return AudioMeta(output_path, duration_ms, "minimax", settings["model"], settings["voice"], speed)


def system_say_synthesize(text: str, output_path: Path, *, speed: float) -> AudioMeta:
    estimated_seconds = max(2.0, len(text) / 7.0)
    speech_rate = str(int(185 * speed))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        aiff_path = Path(tmp) / "voice.aiff"
        result = subprocess.run(["say", "-v", "Tingting", "-r", speech_rate, "-o", str(aiff_path), text])
        if result.returncode == 0 and aiff_path.exists():
            run(["ffmpeg", "-y", "-i", str(aiff_path), "-codec:a", "libmp3lame", str(output_path)])
        else:
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=32000:cl=mono",
                    "-t",
                    f"{estimated_seconds:.2f}",
                    "-q:a",
                    "9",
                    "-acodec",
                    "libmp3lame",
                    str(output_path),
                ]
            )
    duration_ms = probe_audio_duration_ms(output_path) or int(estimated_seconds * 1000)
    settings = tts_settings(speed, "system_say")
    normalize_audio_timing(output_path, settings)
    duration_ms = probe_audio_duration_ms(output_path) or duration_ms
    return AudioMeta(output_path, duration_ms, "system_say", settings["model"], settings["voice"], speed)


def synthesize_audio(
    project_dir: Path,
    plan: Dict[str, Any],
    *,
    speed: float,
    force: bool,
    preview: bool,
) -> Dict[str, AudioMeta]:
    audio_dir = project_dir / "work" / "audio"
    outputs: Dict[str, AudioMeta] = {}
    retries = max(1, int(os.getenv("AI_COACH_TTS_RETRIES", "3")))
    for scene in plan["scenes"]:
        scene_id = scene["id"]
        text = str(scene.get("tts_text") or scene["narration"])
        output = audio_dir / f"{scene_id}.mp3"
        meta_path = audio_dir / f"{scene_id}.json"
        expected = audio_cache_payload(text, speed, "minimax")
        if output.exists() and meta_path.exists() and not force:
            try:
                old = read_json(meta_path)
            except Exception:
                old = {}
            if old == expected and probe_audio_duration_ms(output) > 0:
                outputs[scene_id] = AudioMeta(
                    output,
                    probe_audio_duration_ms(output),
                    old["provider"],
                    old["model"],
                    old["voice"],
                    float(old["speed"]),
                )
                continue
        if preview and os.getenv("AI_COACH_PREVIEW_TRY_MINIMAX", "0").strip() != "1":
            outputs[scene_id] = system_say_synthesize(text, output, speed=speed)
            write_json(meta_path, audio_cache_payload(text, speed, "system_say"))
            continue
        last_error: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                outputs[scene_id] = minimax_synthesize(text, output, speed=speed)
                break
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(1.5)
        else:
            if not preview:
                raise RuntimeError(f"{scene_id} MiniMax TTS failed; formal mode forbids silent fallback") from last_error
            outputs[scene_id] = system_say_synthesize(text, output, speed=speed)
            expected = audio_cache_payload(text, speed, "system_say")
        write_json(meta_path, expected)
    return outputs


def narration_group_cache_payload(
    group_id: str,
    scene_ids: List[str],
    texts: List[str],
    speed: float,
    provider: str,
) -> Dict[str, Any]:
    return {
        "schema": 1,
        "narration_mode": "continuous_group",
        "group_id": group_id,
        "scene_ids": scene_ids,
        "texts": texts,
        "separator": "double_newline",
        **tts_settings(speed, provider),
    }


def detect_scene_boundaries_ms(
    path: Path,
    texts: List[str],
) -> List[int]:
    duration_ms = probe_audio_duration_ms(path)
    if duration_ms <= 0:
        raise RuntimeError(f"continuous narration audio has no duration: {path}")
    if len(texts) <= 1:
        return [0, duration_ms]
    result = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            "silencedetect=noise=-40dB:d=0.16",
            "-f",
            "null",
            "-",
        ]
    )
    starts = [float(value) for value in re.findall(r"silence_start:\s*([0-9.]+)", result.stderr)]
    ends = [
        (float(end), float(length))
        for end, length in re.findall(
            r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)",
            result.stderr,
        )
    ]
    silences = [
        {
            "start": start,
            "end": end,
            "mid": (start + end) / 2.0,
            "duration": length,
        }
        for start, (end, length) in zip(starts, ends)
        if end > 0.12 and start < duration_ms / 1000.0 - 0.12
    ]
    weights = [max(1, len(re.sub(r"[\s，。！？；：、,.!?;:\"“”'‘’]", "", text))) for text in texts]
    total_weight = max(1, sum(weights))
    targets: List[float] = []
    cumulative = 0
    duration_seconds = duration_ms / 1000.0
    for weight in weights[:-1]:
        cumulative += weight
        targets.append(duration_seconds * cumulative / total_weight)
    boundaries = [0.0]
    used: set[int] = set()
    for boundary_index, target in enumerate(targets):
        remaining = len(targets) - boundary_index - 1
        lower = boundaries[-1] + 0.18
        upper = duration_seconds - (remaining + 1) * 0.18
        candidates = [
            (index, silence)
            for index, silence in enumerate(silences)
            if index not in used and lower < silence["mid"] < upper
        ]
        if candidates:
            chosen_index, chosen = min(
                candidates,
                key=lambda item: abs(item[1]["mid"] - target)
                - min(item[1]["duration"], 0.8) * 0.12,
            )
            used.add(chosen_index)
            boundary = float(chosen["mid"])
        else:
            boundary = min(max(target, lower), upper)
        boundaries.append(boundary)
    boundaries.append(duration_seconds)
    result_ms = [int(round(value * 1000)) for value in boundaries]
    result_ms[0] = 0
    result_ms[-1] = duration_ms
    for index in range(1, len(result_ms)):
        result_ms[index] = max(result_ms[index], result_ms[index - 1] + 1)
    return result_ms


def synthesize_continuous_narration(
    project_dir: Path,
    plan: Dict[str, Any],
    *,
    speed: float,
    force: bool,
    preview: bool,
) -> Dict[str, Any]:
    groups = validate_narration_groups(plan)
    if not groups:
        raise ValueError("continuous narration requested without narration_groups")
    scenes_by_id = {scene["id"]: scene for scene in plan["scenes"]}
    audio_dir = project_dir / "work" / "audio_groups"
    retries = max(1, int(os.getenv("AI_COACH_TTS_RETRIES", "3")))
    group_results: List[Dict[str, Any]] = []
    scene_audio: Dict[str, AudioMeta] = {}
    scene_segments: Dict[str, Dict[str, Any]] = {}
    for group in groups:
        group_id = group["id"]
        scene_ids = group["scenes"]
        texts = [str(scenes_by_id[scene_id].get("tts_text") or scenes_by_id[scene_id]["narration"]) for scene_id in scene_ids]
        text = "\n\n".join(texts)
        output = audio_dir / f"{group_id}.mp3"
        meta_path = audio_dir / f"{group_id}.json"
        provider = "system_say" if preview and os.getenv("AI_COACH_PREVIEW_TRY_MINIMAX", "0").strip() != "1" else "minimax"
        expected = narration_group_cache_payload(group_id, scene_ids, texts, speed, provider)
        meta: Optional[AudioMeta] = None
        if output.exists() and meta_path.exists() and not force:
            try:
                old = read_json(meta_path)
            except Exception:
                old = {}
            if old == expected and probe_audio_duration_ms(output) > 0:
                meta = AudioMeta(
                    output,
                    probe_audio_duration_ms(output),
                    old["provider"],
                    old["model"],
                    old["voice"],
                    float(old["speed"]),
                )
        if meta is None and provider == "system_say":
            meta = system_say_synthesize(text, output, speed=speed)
        elif meta is None:
            last_error: Optional[Exception] = None
            for attempt in range(1, retries + 1):
                try:
                    meta = minimax_synthesize(text, output, speed=speed)
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < retries:
                        time.sleep(1.5)
            if meta is None:
                raise RuntimeError(f"{group_id} MiniMax TTS failed") from last_error
        write_json(meta_path, expected)
        boundaries_ms = detect_scene_boundaries_ms(meta.path, texts)
        alignment = {
            "schema": 1,
            "group_id": group_id,
            "audio_sha256": sha256_file(meta.path),
            "scene_ids": scene_ids,
            "boundaries_ms": boundaries_ms,
            "policy": "visual boundaries aligned to natural pauses; audio remains uncut",
        }
        write_json(audio_dir / f"{group_id}.alignment.json", alignment)
        group_result = {
            "id": group_id,
            "scene_ids": scene_ids,
            "audio": meta,
            "boundaries_ms": boundaries_ms,
        }
        group_results.append(group_result)
        for index, scene_id in enumerate(scene_ids):
            start_ms = boundaries_ms[index]
            end_ms = boundaries_ms[index + 1]
            duration_ms = max(1, end_ms - start_ms)
            scene_audio[scene_id] = AudioMeta(
                meta.path,
                duration_ms,
                meta.provider,
                meta.model,
                meta.voice,
                meta.speed,
            )
            scene_segments[scene_id] = {
                "group_id": group_id,
                "path": meta.path,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": duration_ms,
            }
    return {
        "mode": "continuous_groups",
        "groups": group_results,
        "scene_audio": scene_audio,
        "scene_segments": scene_segments,
    }


def cut_source_event(source: Path, output: Path, start: float, end: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, float(end) - float(start))
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{float(start):.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source),
            "-an",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )


def extend_video_tail(input_path: Path, output_path: Path, target_seconds: float) -> Path:
    current = ffprobe_duration_seconds(input_path)
    if current >= target_seconds:
        return input_path
    extra = max(0.1, target_seconds - current)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            f"tpad=stop_mode=clone:stop_duration={extra:.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
    )
    return output_path


def prepare_events(project_dir: Path, plan: Dict[str, Any]) -> Dict[str, Path]:
    sources = source_recordings_by_id(project_dir, plan)
    event_dir = project_dir / "work" / "events"
    outputs: Dict[str, Path] = {}
    for scene in plan["scenes"]:
        visual = scene["visual"]
        if visual["kind"] != "video":
            continue
        scene_id = scene["id"]
        if visual.get("path"):
            outputs[scene_id] = resolve_path(project_dir, visual["path"])
            continue
        source = Path(sources[str(visual["source_id"])]["path"])
        output = event_dir / f"{scene_id}_{visual['semantic_event']}.mp4"
        cut_source_event(source, output, float(visual["in_sec"]), float(visual["out_sec"]))
        visual["path"] = str(output.relative_to(project_dir))
        outputs[scene_id] = output
    return outputs


def validate_recording_durations(
    project_dir: Path,
    plan: Dict[str, Any],
    audio: Dict[str, AudioMeta],
) -> Dict[str, Path]:
    prepared = prepare_events(project_dir, plan)
    adjusted: Dict[str, Path] = {}
    for scene in plan["scenes"]:
        visual = scene["visual"]
        if visual["kind"] != "video":
            continue
        scene_id = scene["id"]
        margin = 1.0 if visual.get("risk") in {"proof", "result", "pdf", "conclusion"} else 0.5
        required = audio[scene_id].duration_ms / 1000.0 + margin
        clip = prepared[scene_id]
        duration = ffprobe_duration_seconds(clip)
        if duration < required:
            clip = extend_video_tail(clip, project_dir / "work" / "events" / f"{scene_id}_extended.mp4", required)
        adjusted[scene_id] = clip
    return adjusted


def normalize_image_to_card(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
    except Exception:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-vf",
                "scale=1376:768:force_original_aspect_ratio=decrease,pad=1376:768:(ow-iw)/2:(oh-ih)/2:white",
                "-frames:v",
                "1",
                str(output),
            ]
        )
        return
    with Image.open(source) as raw:
        image = raw.convert("RGB")
        scale = min(1376 / image.width, 768 / image.height)
        resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
        canvas = Image.new("RGB", (1376, 768), "#FFFFFF")
        canvas.paste(resized, ((1376 - resized.width) // 2, (768 - resized.height) // 2))
        canvas.save(output)


def placeholder_image(output: Path, scene_id: str) -> None:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=white:s=1376x768", "-frames:v", "1", str(output)])
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1376, 768), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 90, 1296, 678), outline="#DADFE8", width=6)
    draw.text((120, 130), f"{scene_id} preview placeholder", fill="#111111")
    image.save(output)


def copy_public(source: Path, slug: str, relative: str) -> str:
    target = PUBLIC_ROOT / slug / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    # Accepted captures can be read-only. Stage and replace the derived copy
    # so a repeated assembly never needs to open a read-only target for writing.
    fd, staged_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(fd)
    staged = Path(staged_name)
    try:
        shutil.copy2(source, staged)
        staged.replace(target)
    finally:
        staged.unlink(missing_ok=True)
    return f"ai-coach-daily-demo/{slug}/{relative}"


def split_caption_text(text: str, *, max_chars: int = 18, min_chars: int = 4) -> List[str]:
    cleaned = re.sub(r"\s+", "", text.strip())
    if not cleaned:
        return []
    # A full stop is also used as the decimal separator in financial figures.
    # Protect digit-dot-digit runs so captions never turn 1.95% into 195%.
    decimal_dot = "\ue000"
    cleaned = re.sub(r"(?<=\d)\.(?=\d)", decimal_dot, cleaned)
    clauses = [
        part.replace(decimal_dot, ".")
        for part in re.split(r"(?<=[，。！？；：,.!?;:])", cleaned)
        if part
    ]
    chunks: List[str] = []
    for clause in clauses:
        clause = clause.strip("，。！？；：,.!?;:")
        while len(clause) > max_chars:
            split_at = -1
            for mark in "，、：；,;":
                idx = clause.rfind(mark, min_chars, max_chars + 1)
                if idx >= min_chars:
                    split_at = idx + 1
                    break
            if split_at < 0:
                split_at = max_chars
            # Keep financial figures and English names intact at line changes.
            # A hard character boundary used to show "1" then "7%", or
            # "RedSki" then "ll", even though the full narration was correct.
            for token in re.finditer(r"[A-Za-z0-9]+(?:[.\-_][A-Za-z0-9]+)*[%％]?", clause):
                if token.start() < split_at < token.end():
                    split_at = token.start() if token.start() else token.end()
                    break
            chunks.append(clause[:split_at].strip("，。！？；：,.!?;:"))
            clause = clause[split_at:].strip()
        if clause:
            chunks.append(clause)
    merged: List[str] = []
    for chunk in [chunk for chunk in chunks if chunk]:
        if len(chunk) < min_chars and merged and len(merged[-1] + chunk) <= max_chars:
            merged[-1] = f"{merged[-1]}{chunk}"
        else:
            merged.append(chunk)
    return merged


def caption_segments(text: str, *, audio_duration_ms: int, duration_frames: int) -> List[Dict[str, int | str]]:
    chunks = split_caption_text(text)
    if not chunks:
        return []
    audio_frames = max(1, int(round(audio_duration_ms / 1000.0 * FPS)))
    total_frames = max(1, min(duration_frames, audio_frames + 4))
    weights = [max(4, len(chunk)) for chunk in chunks]
    total_weight = max(1, sum(weights))
    segments: List[Dict[str, int | str]] = []
    cursor = 0
    for index, (chunk, weight) in enumerate(zip(chunks, weights)):
        if index == len(chunks) - 1:
            end = duration_frames
        else:
            span = max(18, int(round(total_frames * weight / total_weight)))
            remaining = len(chunks) - index - 1
            end = min(cursor + span, total_frames - remaining * 18)
        end = max(cursor + 1, end)
        segments.append({"text": chunk, "startFrame": cursor, "endFrame": end})
        cursor = end
    segments[-1]["endFrame"] = duration_frames
    return segments


def prepare_bgm(plan: Dict[str, Any], slug: str, copy_asset=copy_public) -> Optional[Dict[str, Any]]:
    """Resolve required music and fail instead of silently producing a music-free video."""
    config = plan.get("bgm") or {}
    if config.get("enabled", True) is False:
        if not str(config.get("omission_reason") or "").strip():
            raise ValueError("BGM is required; disabling it needs the user's explicit omission_reason")
        return None
    source = Path(config.get("path") or DEFAULT_BGM_PATH).expanduser().resolve()
    volume = float(config.get("volume", 0.15))
    if not source.is_file():
        raise ValueError(f"Required BGM file is missing: {source}")
    if not math.isfinite(volume) or not 0 < volume <= 1:
        raise ValueError("Required BGM volume must be > 0 and <= 1")
    duration = ffprobe_duration_seconds(source)
    if duration <= 0:
        raise ValueError(f"Required BGM is not a playable audio file: {source}")
    fades = {key: float(config.get(key, default)) for key, default in
             [("fadeInSeconds", 0.8), ("fadeOutSeconds", 1.6)]}
    if any(not math.isfinite(value) or value < 0 for value in fades.values()):
        raise ValueError("BGM fades must be finite and non-negative")
    return {
        "path": copy_asset(source, slug, f"music/{source.name}"),
        "volume": volume,
        "durationSeconds": duration,
        "sourcePath": str(source),
        "sha256": sha256_file(source),
        **fades,
    }


def prepare_remotion_data(
    project_dir: Path,
    plan: Dict[str, Any],
    audio: Dict[str, AudioMeta],
    clips: Dict[str, Path],
    *,
    render_dir: Path,
    preview: bool,
    continuous_narration: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    plan = apply_brand_defaults(plan, project_dir=project_dir)
    slug = public_slug(plan["topic"])
    shutil.rmtree(PUBLIC_ROOT / slug, ignore_errors=True)
    logo_source = Path(plan.get("logo_image") or DEFAULT_LOGO_IMAGE).expanduser().resolve()
    corner_logo_config = plan.get("corner_logo") or {}
    if not isinstance(corner_logo_config, dict):
        corner_logo_config = {}
    corner_logo_raw = (
        corner_logo_config.get("path")
        or plan.get("corner_logo_image")
        or DEFAULT_CORNER_LOGO_IMAGE
    )
    corner_logo = Path(corner_logo_raw).expanduser().resolve()
    corner_logo_width = int(corner_logo_config.get("width") or plan.get("corner_logo_width") or 136)
    corner_logo_height = int(corner_logo_config.get("height") or plan.get("corner_logo_height") or 136)
    corner_logo_background = corner_logo_config.get("background")
    corner_logo_padding_x = int(corner_logo_config.get("padding_x") or 0)
    corner_logo_padding_y = int(corner_logo_config.get("padding_y") or 0)
    corner_logo_border_radius = int(corner_logo_config.get("border_radius") or 0)
    logo_asset = copy_public(logo_source, slug, f"images/{logo_source.name}") if logo_source.exists() else None
    corner_asset = copy_public(corner_logo, slug, f"images/{corner_logo.name}") if corner_logo.exists() else None
    bgm_payload = prepare_bgm(plan, slug)

    rendered_images: Dict[str, List[Path]] = {}
    scenes_by_id = {scene["id"]: scene for scene in plan["scenes"]}

    def resolved_visual_kind(scene: Dict[str, Any]) -> str:
        visual = scene["visual"]
        visited: set[str] = set()
        while visual["kind"] == "reuse":
            target_id = str(visual["reuse_of"])
            if target_id in visited:
                raise ValueError(f"visual reuse cycle at {target_id}")
            visited.add(target_id)
            visual = scenes_by_id[target_id]["visual"]
        return "video" if visual["kind"] == "video" else "image"

    for scene in plan["scenes"]:
        visual = scene["visual"]
        scene_id = scene["id"]
        if visual["kind"] == "reuse":
            rendered_images[scene_id] = rendered_images[str(visual["reuse_of"])]
        elif visual["kind"] == "image":
            source = resolve_path(project_dir, visual["path"])
            if scene["layout"] == "recording":
                output = render_dir / "images" / f"{scene_id}{source.suffix.lower()}"
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
            else:
                output = render_dir / "images" / f"{scene_id}.png"
                normalize_image_to_card(source, output)
            rendered_images[scene_id] = [output]
        elif visual["kind"] == "sequence":
            rendered_images[scene_id] = []
            for index, item in enumerate(visual.get("items", []), 1):
                source = resolve_path(project_dir, item["path"])
                if scene["layout"] == "recording":
                    output = render_dir / "images" / f"{scene_id}_{index:02d}{source.suffix.lower()}"
                    output.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, output)
                else:
                    output = render_dir / "images" / f"{scene_id}_{index:02d}.png"
                    normalize_image_to_card(source, output)
                rendered_images[scene_id].append(output)
        elif preview and scene["layout"] == "illustration":
            output = render_dir / "images" / f"{scene_id}.png"
            placeholder_image(output, scene_id)
            rendered_images[scene_id] = [output]

    audio_assets = {}
    narration_tracks: List[Dict[str, Any]] = []
    continuous_segments: Dict[str, Dict[str, Any]] = {}
    continuous_groups: Dict[str, Dict[str, Any]] = {}
    if continuous_narration:
        continuous_segments = continuous_narration["scene_segments"]
        continuous_groups = {group["id"]: group for group in continuous_narration["groups"]}
        for group in continuous_narration["groups"]:
            meta = group["audio"]
            group["public_path"] = copy_public(meta.path, slug, f"audio_groups/{group['id']}.mp3")
    else:
        audio_assets = {
            scene_id: copy_public(meta.path, slug, f"audio/{meta.path.name}")
            for scene_id, meta in audio.items()
        }
    image_assets = {
        scene_id: [copy_public(path, slug, f"images/{path.name}") for path in paths]
        for scene_id, paths in rendered_images.items()
    }
    clip_assets = {
        scene_id: copy_public(path, slug, f"clips/{path.name}")
        for scene_id, path in clips.items()
    }

    scene_payload: List[Dict[str, Any]] = []
    cursor_frames = 0
    started_groups: set[str] = set()
    for scene in plan["scenes"]:
        scene_id = scene["id"]
        visual = scene["visual"]
        kind = resolved_visual_kind(scene)
        segment = continuous_segments.get(scene_id)
        if segment:
            group = continuous_groups[segment["group_id"]]
            boundaries = group["boundaries_ms"]
            boundary_frames = [int(round(value / 1000.0 * FPS)) for value in boundaries]
            boundary_frames[-1] = max(boundary_frames[-1], int(math.ceil(group["audio"].duration_ms / 1000.0 * FPS)))
            segment_index = group["scene_ids"].index(scene_id)
            segment_frames = max(1, boundary_frames[segment_index + 1] - boundary_frames[segment_index])
            duration_frames = segment_frames
            if group["id"] not in started_groups:
                narration_tracks.append(
                    {
                        "id": group["id"],
                        "path": group["public_path"],
                        "startFrame": cursor_frames,
                        "durationFrames": max(1, boundary_frames[-1]),
                    }
                )
                started_groups.add(group["id"])
            audio_frames = segment_frames
        else:
            audio_frames = audio_duration_frames(audio[scene_id].duration_ms)
        if segment:
            if kind == "video":
                video_seconds = ffprobe_duration_seconds(clips[scene_id])
                asset_path = clip_assets[scene_id]
            else:
                paths = image_assets[scene_id]
                asset_path = paths[0]
        elif kind == "video":
            video_seconds = ffprobe_duration_seconds(clips[scene_id])
            video_frames = max(1, int(round(video_seconds * FPS)))
            if video_frames < audio_frames:
                raise RuntimeError(
                    f"{scene_id} video is shorter than its source audio timeline: "
                    f"{video_frames} < {audio_frames} frames"
                )
            duration_frames = audio_frames
            asset_path = clip_assets[scene_id]
        else:
            duration_frames = audio_frames
            paths = image_assets[scene_id]
            asset_path = paths[0]
        item: Dict[str, Any] = {
            "id": scene_id,
            "kind": kind,
            "layout": scene["layout"],
            "headline": "",
            "caption": scene.get("caption") or scene["narration"],
            "captionSegments": caption_segments(
                scene["narration"],
                audio_duration_ms=audio[scene_id].duration_ms,
                duration_frames=duration_frames,
            ),
            "assetPath": asset_path,
            "durationFrames": duration_frames,
        }
        if not segment:
            item["audioPath"] = audio_assets[scene_id]
        if kind == "image" and len(image_assets[scene_id]) > 1:
            item["assetPaths"] = image_assets[scene_id]
        if kind == "video":
            item["videoDurationSeconds"] = ffprobe_duration_seconds(clips[scene_id])
        scene_payload.append(item)
        cursor_frames += duration_frames

    return {
        "meta": {
            "seriesTitle": plan.get("series_title") or SERIES_TITLE,
            "episode": str(plan.get("episode") or "01"),
            "showEpisodeMarker": bool(plan.get("show_episode_marker", True)),
            "demoTitle": plan.get("topic") or "",
            "fps": FPS,
            "width": 1080,
            "height": 1920,
            "logoPath": logo_asset,
            "cornerLogoPath": corner_asset,
            "cornerLogoWidth": corner_logo_width,
            "cornerLogoHeight": corner_logo_height,
            "cornerLogoBackground": corner_logo_background,
            "cornerLogoPaddingX": corner_logo_padding_x,
            "cornerLogoPaddingY": corner_logo_padding_y,
            "cornerLogoBorderRadius": corner_logo_border_radius,
            "bgm": bgm_payload,
        },
        "scenes": scene_payload,
        "narrationTracks": narration_tracks,
    }


def render_remotion(output_path: Path, props_path: Path) -> None:
    if not (REMOTION_DIR / "node_modules").exists():
        run(["npm", "install"], cwd=REMOTION_DIR)
    run(["npm", "run", "typecheck"], cwd=REMOTION_DIR)
    run(
        [
            "npx",
            "remotion",
            "render",
            "AiCoachDailyDemo",
            str(output_path),
            "--props",
            str(props_path),
            "--codec",
            "h264",
            "--crf",
            "16",
        ],
        cwd=REMOTION_DIR,
    )


def validate_final_media(path: Path) -> Dict[str, Any]:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"candidate missing or empty: {path}")
    probe = ffprobe(path)
    streams = probe.get("streams") or []
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if not video:
        raise RuntimeError("candidate has no video stream")
    if not audio:
        raise RuntimeError("candidate has no audio stream")
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    codec = str(video.get("codec_name") or "")
    rate_raw = str(video.get("avg_frame_rate") or "0/1")
    numerator, _, denominator = rate_raw.partition("/")
    fps = float(numerator or 0) / max(float(denominator or 1), 1.0)
    duration = float((probe.get("format") or {}).get("duration") or 0.0)
    errors = []
    if (width, height) != (1080, 1920):
        errors.append(f"expected 1080x1920, got {width}x{height}")
    if codec != "h264":
        errors.append(f"expected h264, got {codec}")
    if not 29.0 <= fps <= 31.0:
        errors.append(f"expected 30fps, got {fps:.3f}")
    if duration <= 0:
        errors.append("zero duration")
    if errors:
        raise RuntimeError("; ".join(errors))
    return {
        "width": width,
        "height": height,
        "video_codec": codec,
        "audio_codec": audio.get("codec_name"),
        "fps": round(fps, 3),
        "duration_seconds": round(duration, 3),
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def extract_frame(video: Path, output: Path, timestamp: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-ss", f"{max(0.0, timestamp):.3f}", "-i", str(video), "-frames:v", "1", str(output)])


def extract_qa_frames(project_dir: Path, plan: Dict[str, Any], video: Path, remotion_data: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, List[str]]:
    qa_root = project_dir / "work" / "qa_frames_latest"
    shutil.rmtree(qa_root, ignore_errors=True)
    final_quality = qa_root / "final_quality"
    key_events = qa_root / "key_events"
    boundaries = qa_root / "boundaries"
    outputs: Dict[str, List[str]] = {"final_quality": [], "key_events": [], "boundaries": []}
    duration = float(media["duration_seconds"])
    for label, ratio in (("10pct", 0.10), ("50pct", 0.50), ("90pct", 0.90)):
        out = final_quality / f"final_{label}.png"
        extract_frame(video, out, duration * ratio)
        outputs["final_quality"].append(str(out))
    cursor = 0.0
    for scene, rendered in zip(plan["scenes"], remotion_data["scenes"]):
        scene_seconds = rendered["durationFrames"] / FPS
        if rendered["kind"] == "video":
            out = key_events / f"{scene['id']}_{scene['visual']['semantic_event']}.png"
            extract_frame(video, out, cursor + min(scene_seconds * 0.5, max(scene_seconds - 0.1, 0)))
            outputs["key_events"].append(str(out))
        if scene["id"] != "scene_01":
            for offset, label in ((-0.08, "before"), (0.08, "after")):
                out = boundaries / f"{scene['id']}_{label}.png"
                extract_frame(video, out, cursor + offset)
                outputs["boundaries"].append(str(out))
        cursor += scene_seconds
    return outputs


def build_scene_bindings(
    project_dir: Path,
    plan: Dict[str, Any],
    audio: Dict[str, AudioMeta],
    clips: Dict[str, Path],
    remotion_data: Dict[str, Any],
    continuous_narration: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    bindings: List[Dict[str, Any]] = []
    for scene, rendered in zip(plan["scenes"], remotion_data["scenes"]):
        scene_id = scene["id"]
        visual = scene["visual"]
        if visual["kind"] == "reuse":
            visual_kind = "reuse"
            visual_paths = []
            visual_sha = []
            source = {"reuse_of": visual["reuse_of"]}
        elif rendered["kind"] == "video":
            clip = clips[scene_id]
            visual_kind = "video"
            visual_paths = [str(clip)]
            visual_sha = [sha256_file(clip)]
            source = {
                "source_id": visual.get("source_id"),
                "in_sec": visual.get("in_sec"),
                "out_sec": visual.get("out_sec"),
                "semantic_event": visual.get("semantic_event"),
                "required_evidence": visual.get("required_evidence"),
                "continuity_group": visual.get("continuity_group"),
                "risk": visual.get("risk"),
            }
        else:
            paths = visual_paths_for_hash(project_dir, scene)
            visual_kind = visual["kind"]
            visual_paths = [str(path) for path in paths]
            visual_sha = [sha256_file(path) for path in paths]
            source = {"approval": visual.get("approval")}
        binding = {
                "scene_id": scene_id,
                "layout": scene["layout"],
                "narration_sha256": sha256_text(scene["narration"]),
                "visual_kind": visual_kind,
                "visual_paths": visual_paths,
                "visual_sha256": visual_sha,
                "source_evidence": source,
                "audio_path": str(audio[scene_id].path),
                "audio_sha256": sha256_file(audio[scene_id].path),
                "audio_duration_ms": audio[scene_id].duration_ms,
                "duration_frames": rendered["durationFrames"],
            }
        if continuous_narration:
            segment = continuous_narration["scene_segments"][scene_id]
            binding.update(
                {
                    "narration_mode": "continuous_groups",
                    "narration_group_id": segment["group_id"],
                    "group_audio_path": str(segment["path"]),
                    "group_audio_sha256": sha256_file(segment["path"]),
                    "group_audio_start_ms": segment["start_ms"],
                    "group_audio_end_ms": segment["end_ms"],
                    "audio_policy": "uncut continuous track; visuals align to natural pauses",
                }
            )
        bindings.append(binding)
    return {
        "schema": 1,
        "scene_count": len(bindings),
        "narration_mode": "continuous_groups" if continuous_narration else "per_scene",
        "scenes": bindings,
    }


def render_fingerprint(plan: Dict[str, Any], bindings: Dict[str, Any], *, speed: float) -> str:
    payload = {
        "schema": SCHEMA_VERSION,
        "topic": plan.get("topic"),
        "episode": plan.get("episode"),
        "series_title": plan.get("series_title") or SERIES_TITLE,
        "show_episode_marker": bool(plan.get("show_episode_marker", True)),
        "script": script_fingerprint(plan["scenes"]),
        "visuals": bindings,
        "tts": tts_settings(speed, "minimax"),
        "audio_timing": audio_timing_settings(),
        "bgm": plan.get("bgm") or None,
        "corner_logo": plan.get("corner_logo") or plan.get("corner_logo_image") or None,
        "layout_policy": "fixed-stage-v2",
        "transition_policy": "clean-cut-v1",
    }
    return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))[:16]


def write_recording_event_map(project_dir: Path, plan: Dict[str, Any], clips: Optional[Dict[str, Path]] = None) -> Path:
    rows = [
        "| Scene | Narration claim | Semantic event | Source | In-out timecode | Required visible evidence | Continuity group | Clip path | QA status |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for scene in plan["scenes"]:
        visual = scene["visual"]
        if visual["kind"] != "video":
            continue
        clip_path = clips.get(scene["id"]) if clips else None
        rows.append(
            "| {scene} | {claim} | {event} | {source} | {start}-{end} | {evidence} | {group} | {clip} | pending |".format(
                scene=scene["id"],
                claim=scene["narration"].replace("|", "／"),
                event=visual.get("semantic_event", ""),
                source=visual.get("source_id", ""),
                start=visual.get("in_sec", ""),
                end=visual.get("out_sec", ""),
                evidence=str(visual.get("required_evidence", "")).replace("|", "／"),
                group=visual.get("continuity_group", ""),
                clip=str(clip_path or visual.get("path") or ""),
            )
        )
    path = project_dir / "recording_event_map.md"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def write_qa_report(project_dir: Path, render_dir: Path, media: Dict[str, Any], frames: Dict[str, List[str]], *, promoted: bool = False) -> None:
    lines = [
        "# AI Coach QA Report",
        "",
        "## Automated media gate",
        "",
        "- Status: PASS",
        f"- Resolution: {media['width']}x{media['height']}",
        f"- Video codec: {media['video_codec']}",
        f"- Audio codec: {media['audio_codec']}",
        f"- Frame rate: {media['fps']} fps",
        f"- Duration: {media['duration_seconds']} seconds",
        f"- SHA-256: `{media['sha256']}`",
        "",
        "## QA frames",
        "",
        *[f"- final_quality: `{path}`" for path in frames.get("final_quality", [])],
        *[f"- key_event: `{path}`" for path in frames.get("key_events", [])],
        *[f"- boundary: `{path}`" for path in frames.get("boundaries", [])],
        "",
        "## Manual gate",
        "",
        f"- Promoted with manual QA approval: {'yes' if promoted else 'no'}",
        "- Check full playback at normal speed before promotion.",
        "- Check recording readability and subtitle position.",
        "- Check narration-to-picture truth for every recording scene.",
        "- Check PDF arrival/open/browse continuity when applicable.",
        "",
    ]
    (render_dir / "qa_report.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(render_dir / "qa_report.json", {"media": media, "frames": frames, "promoted": promoted})


def render_candidate(
    project_dir: Path,
    *,
    speed: float,
    force_audio: bool,
    preview: bool,
    corner_logo_variant: Optional[str] = None,
) -> Path:
    plan = validate_plan(project_dir, allow_unapproved=preview)
    plan = apply_corner_logo_variant(plan, corner_logo_variant)
    plan = apply_brand_defaults(plan, project_dir=project_dir)
    continuous_narration = None
    if plan.get("narration_groups"):
        continuous_narration = synthesize_continuous_narration(
            project_dir, plan, speed=speed, force=force_audio, preview=preview
        )
        audio = continuous_narration["scene_audio"]
    else:
        audio = synthesize_audio(project_dir, plan, speed=speed, force=force_audio, preview=preview)
    clips = validate_recording_durations(project_dir, plan, audio)
    render_seed = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "script": script_fingerprint(plan["scenes"]),
        "preview": preview,
        "render_variant": plan.get("_render_variant"),
    }
    render_id = sha256_text(json.dumps(render_seed, ensure_ascii=False, sort_keys=True))[:16]
    render_dir = project_dir / "work" / "render" / render_id
    render_dir.mkdir(parents=True, exist_ok=True)
    remotion_data = prepare_remotion_data(
        project_dir,
        plan,
        audio,
        clips,
        render_dir=render_dir,
        preview=preview,
        continuous_narration=continuous_narration,
    )
    props_path = render_dir / "remotion_props.json"
    write_json(props_path, {"data": remotion_data})
    write_json(render_dir / "remotion_data.json", remotion_data)
    bindings = build_scene_bindings(
        project_dir, plan, audio, clips, remotion_data, continuous_narration=continuous_narration
    )
    version_id = render_fingerprint(plan, bindings, speed=speed)
    bindings["render_version_id"] = version_id
    write_json(render_dir / "scene_bindings.json", bindings)
    write_json(render_dir / "scene_plan.lock.json", plan)
    write_recording_event_map(project_dir, plan, clips)
    output = render_dir / ("video_preview.mp4" if preview else "video_candidate.mp4")
    render_remotion(output, props_path)
    media = validate_final_media(output)
    frames = extract_qa_frames(project_dir, plan, output, remotion_data, media)
    manifest = {
        "schema": 1,
        "render_version_id": version_id,
        "render_dir": str(render_dir),
        "candidate": str(output),
        "candidate_sha256": sha256_file(output),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "preview": preview,
        "media": media,
        "tts": tts_settings(speed, "minimax"),
        "audio_timing": audio_timing_settings(),
        "script_sha256": script_fingerprint(plan["scenes"]),
        "scene_plan_sha256": sha256_file(project_dir / "scene_plan.json"),
        "manual_qa_required": not preview,
        "narration_mode": "continuous_groups" if continuous_narration else "per_scene",
        "render_variant": plan.get("_render_variant"),
    }
    if continuous_narration:
        manifest["narration_groups"] = [
            {
                "id": group["id"],
                "scene_ids": group["scene_ids"],
                "audio_path": str(group["audio"].path),
                "audio_sha256": sha256_file(group["audio"].path),
                "duration_ms": group["audio"].duration_ms,
                "boundaries_ms": group["boundaries_ms"],
                "policy": "uncut continuous track",
            }
            for group in continuous_narration["groups"]
        ]
    write_json(render_dir / "render_manifest.json", manifest)
    write_qa_report(project_dir, render_dir, media, frames, promoted=False)
    if not preview:
        latest = project_dir / "work" / "render" / "latest_candidate.txt"
        latest.write_text(str(render_dir), encoding="utf-8")
        variant = plan.get("_render_variant") or {}
        if variant.get("id"):
            variant_latest = project_dir / "work" / "render" / f"latest_candidate_{variant['id']}.txt"
            variant_latest.write_text(str(render_dir), encoding="utf-8")
    print(output)
    return output


def archive_previous_delivery(project_dir: Path) -> Optional[Path]:
    generated_names = {
        "video.mp4",
        "render_manifest.json",
        "scene_bindings.json",
        "qa_report.json",
        "qa_report.md",
        "口播文案_成片版.txt",
    }
    candidates = [path for path in project_dir.iterdir() if path.is_file() and path.name in generated_names]
    candidates.extend(
        path
        for pattern in ("video_*.mp4", "video-*.mp4", "preview*.mp4")
        for path in project_dir.glob(pattern)
        if path.is_file() and path.name != "video.mp4"
    )
    if not candidates:
        return None
    archive = project_dir / "work" / "archive" / datetime.now().strftime("%Y%m%d-%H%M%S")
    archive.mkdir(parents=True, exist_ok=True)
    for path in sorted(set(candidates)):
        shutil.move(str(path), archive / path.name)
    return archive


def standard_delivery_root(project_dir: Path) -> Optional[Path]:
    project_dir = project_dir.expanduser().resolve()
    if project_dir.name == "03_制作" and project_dir.parent.name == "视频":
        return project_dir.parent / "04_交付"
    return None


def _max_delivery_version(history_root: Path, current_root: Path) -> int:
    versions: List[int] = []
    if current_root.is_dir():
        delivery = current_root / "delivery.json"
        if delivery.is_file():
            try:
                versions.append(int(read_json(delivery).get("delivery_version") or 0))
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
    if history_root.is_dir():
        for child in history_root.iterdir():
            match = re.match(r"^v(\d+)-", child.name)
            if match:
                versions.append(int(match.group(1)))
    return max(versions, default=0)


def sync_standard_delivery(project_dir: Path) -> Optional[Path]:
    """Mirror a promoted standard Caishu project into the single human-facing delivery slot."""
    delivery_root = standard_delivery_root(project_dir)
    if delivery_root is None:
        return None
    current = delivery_root / "当前"
    history = delivery_root / "历史"
    history.mkdir(parents=True, exist_ok=True)
    previous_version = _max_delivery_version(history, current)
    if current.is_dir() and any(current.iterdir()):
        old_delivery = current / "delivery.json"
        archived_version = previous_version or 1
        if old_delivery.is_file():
            try:
                archived_version = int(read_json(old_delivery).get("delivery_version") or archived_version)
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        archive_dir = history / f"v{archived_version:02d}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if archive_dir.exists():
            raise FileExistsError(archive_dir)
        shutil.move(str(current), str(archive_dir))
    current.mkdir(parents=True, exist_ok=True)
    new_version = previous_version + 1
    copied: Dict[str, Any] = {}
    for name in (
        "video.mp4",
        "口播文案_成片版.txt",
        "render_manifest.json",
        "scene_bindings.json",
        "qa_report.json",
        "qa_report.md",
    ):
        source = project_dir / name
        if not source.is_file():
            continue
        target = current / name
        shutil.copy2(source, target)
        copied[name] = {
            "path": str(target),
            "sha256": sha256_file(target),
            "bytes": target.stat().st_size,
        }
    if "video.mp4" not in copied:
        raise FileNotFoundError(project_dir / "video.mp4")
    payload = {
        "schema_version": 1,
        "delivery_version": new_version,
        "promoted_at": datetime.now().isoformat(timespec="seconds"),
        "source_project_dir": str(project_dir),
        "files": copied,
    }
    write_json(current / "delivery.json", payload)
    return current


def archive_creation_delivery(project_dir: Path) -> None:
    """Archive a promoted production project without blocking the completed delivery."""
    resolved_project = project_dir.resolve()
    is_archivable_project = False
    for root in ARCHIVABLE_PROJECT_ROOTS:
        try:
            resolved_project.relative_to(root.resolve())
            is_archivable_project = True
            break
        except ValueError:
            continue
    if not is_archivable_project:
        return
    if not CREATION_ARCHIVE_HOOK.exists():
        print(f"⚠️ 创作知识库归档钩子不存在: {CREATION_ARCHIVE_HOOK}")
        return
    plan = load_plan(project_dir)
    profile = resolve_brand_profile(plan, project_dir=project_dir)
    brand_id = {
        "caishu_ai_lab": "caishu-ai-lab",
        "miaodong_finance": "miaodong-finance",
    }[profile]
    result = subprocess.run(
        [
            sys.executable,
            str(CREATION_ARCHIVE_HOOK),
            "--brand",
            brand_id,
            "--content-type",
            "video-script",
            "--title",
            str(plan.get("topic") or project_dir.name),
            "--source",
            str(project_dir / "口播文案_成片版.txt"),
            "--project",
            str(project_dir),
            "--event",
            "delivered",
            "--artifact",
            str(project_dir / "video.mp4"),
            "--proof",
            str(project_dir / "render_manifest.json"),
            "--platform",
            "短视频",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        print("✓ 成片口播已归档到“我的创作知识库”")
    else:
        print(f"⚠️ 成片已交付，但知识库归档待重试: {project_dir / 'archive_pending.json'}")


def promote(project_dir: Path, *, render_dir: Optional[Path], approve_manual_qa: bool) -> Path:
    if not approve_manual_qa:
        raise RuntimeError("promote requires --approve-manual-qa")
    if render_dir is None:
        latest = project_dir / "work" / "render" / "latest_candidate.txt"
        if not latest.exists():
            raise FileNotFoundError("no latest candidate found")
        render_dir = Path(latest.read_text(encoding="utf-8").strip()).expanduser().resolve()
    candidate = render_dir / "video_candidate.mp4"
    manifest_path = render_dir / "render_manifest.json"
    bindings_path = render_dir / "scene_bindings.json"
    qa_md = render_dir / "qa_report.md"
    qa_json = render_dir / "qa_report.json"
    for path in (candidate, manifest_path, bindings_path, qa_md, qa_json):
        if not path.exists():
            raise FileNotFoundError(f"missing candidate artifact: {path}")
    manifest = read_json(manifest_path)
    actual_hash = sha256_file(candidate)
    if manifest.get("candidate_sha256") != actual_hash:
        raise RuntimeError("candidate hash changed after render")
    media = validate_final_media(candidate)
    plan = load_plan(project_dir)
    script = "\n".join(f"{scene['id']}｜{scene['narration']}" for scene in plan["scenes"])
    archive_previous_delivery(project_dir)
    os.replace(candidate, project_dir / "video.mp4")
    shutil.copy2(bindings_path, project_dir / "scene_bindings.json")
    shutil.copy2(manifest_path, project_dir / "render_manifest.json")
    shutil.copy2(qa_md, project_dir / "qa_report.md")
    shutil.copy2(qa_json, project_dir / "qa_report.json")
    (project_dir / "口播文案_成片版.txt").write_text(script + "\n", encoding="utf-8")
    manifest["promoted_at"] = datetime.now().isoformat(timespec="seconds")
    manifest["video"] = {"path": str(project_dir / "video.mp4"), **media}
    write_json(project_dir / "render_manifest.json", manifest)
    qa_text = (project_dir / "qa_report.md").read_text(encoding="utf-8")
    qa_text = qa_text.replace("Promoted with manual QA approval: no", "Promoted with manual QA approval: yes")
    (project_dir / "qa_report.md").write_text(qa_text, encoding="utf-8")
    qa_payload = read_json(project_dir / "qa_report.json")
    qa_payload["promoted"] = True
    qa_payload["promoted_at"] = manifest["promoted_at"]
    write_json(project_dir / "qa_report.json", qa_payload)
    delivery_dir = sync_standard_delivery(project_dir)
    if delivery_dir is not None:
        print(f"✓ 标准交付已同步: {delivery_dir / 'video.mp4'}")
    archive_creation_delivery(project_dir)
    print(project_dir / "video.mp4")
    return project_dir / "video.mp4"


def approve_image(project_dir: Path, scene_id: str, image_path: Path) -> None:
    plan = load_plan(project_dir)
    image_path = image_path.expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    for scene in plan["scenes"]:
        if scene["id"] == scene_id:
            visual = scene["visual"]
            if visual["kind"] != "image":
                raise ValueError(f"{scene_id} is not an image scene")
            visual["path"] = str(image_path)
            visual["approval"] = {
                "status": "approved",
                "sha256": sha256_file(image_path),
                "approved_at": datetime.now().isoformat(timespec="seconds"),
            }
            write_json(project_dir / "scene_plan.json", plan)
            return
    raise ValueError(f"unknown scene: {scene_id}")


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project).expanduser().resolve()
    plan = validate_plan(project_dir, allow_unapproved=args.allow_unapproved)
    write_recording_event_map(project_dir, plan)
    print("validate PASS")
    return 0


def command_prepare_events(args: argparse.Namespace) -> int:
    project_dir = Path(args.project).expanduser().resolve()
    plan = validate_plan(project_dir, allow_unapproved=args.allow_unapproved)
    clips = prepare_events(project_dir, plan)
    write_json(project_dir / "work" / "events" / "prepared_events.json", {key: str(value) for key, value in clips.items()})
    write_recording_event_map(project_dir, plan, clips)
    print(project_dir / "work" / "events" / "prepared_events.json")
    return 0


def command_candidate(args: argparse.Namespace, *, preview: bool) -> int:
    project_dir = Path(args.project).expanduser().resolve()
    if args.corner_logo_variant:
        outputs = [
            render_candidate(
                project_dir,
                speed=args.tts_speed,
                force_audio=args.force_audio,
                preview=preview,
                corner_logo_variant=args.corner_logo_variant,
            )
        ]
    else:
        plan = load_plan(project_dir)
        variant_ids = default_corner_logo_variant_ids(plan) if (args.all_logo_variants or not preview) else []
        outputs = []
        if variant_ids:
            for variant_id in variant_ids:
                outputs.append(
                    render_candidate(
                        project_dir,
                        speed=args.tts_speed,
                        force_audio=args.force_audio,
                        preview=preview,
                        corner_logo_variant=variant_id,
                    )
                )
        else:
            outputs.append(
                render_candidate(
                    project_dir,
                    speed=args.tts_speed,
                    force_audio=args.force_audio,
                    preview=preview,
                )
            )
    if len(outputs) > 1 and not preview:
        payload = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "candidates": [str(path) for path in outputs],
        }
        write_json(project_dir / "work" / "render" / "latest_candidates.json", payload)
    return 0


def command_promote(args: argparse.Namespace) -> int:
    project_dir = Path(args.project).expanduser().resolve()
    render_dir = Path(args.render_dir).expanduser().resolve() if args.render_dir else None
    promote(project_dir, render_dir=render_dir, approve_manual_qa=args.approve_manual_qa)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Coach Daily Demo fixed-30-scene workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate")
    validate_p.add_argument("--project", required=True)
    validate_p.add_argument("--allow-unapproved", action="store_true")
    validate_p.set_defaults(func=command_validate)

    approve_p = sub.add_parser("approve-image")
    approve_p.add_argument("--project", required=True)
    approve_p.add_argument("--scene-id", required=True)
    approve_p.add_argument("--image", required=True)
    approve_p.set_defaults(func=lambda args: (approve_image(Path(args.project).expanduser().resolve(), args.scene_id, Path(args.image)), 0)[1])

    prepare_p = sub.add_parser("prepare-events")
    prepare_p.add_argument("--project", required=True)
    prepare_p.add_argument("--allow-unapproved", action="store_true")
    prepare_p.set_defaults(func=command_prepare_events)

    preview_p = sub.add_parser("preview")
    preview_p.add_argument("--project", required=True)
    preview_p.add_argument("--tts-speed", type=float, default=float(os.getenv("AI_COACH_TTS_SPEED", "1.13")))
    preview_p.add_argument("--force-audio", action="store_true")
    preview_p.add_argument("--corner-logo-variant")
    preview_p.add_argument("--all-logo-variants", action="store_true")
    preview_p.set_defaults(func=lambda args: command_candidate(args, preview=True))

    candidate_p = sub.add_parser("candidate")
    candidate_p.add_argument("--project", required=True)
    candidate_p.add_argument("--tts-speed", type=float, default=float(os.getenv("AI_COACH_TTS_SPEED", "1.13")))
    candidate_p.add_argument("--force-audio", action="store_true")
    candidate_p.add_argument("--corner-logo-variant")
    candidate_p.add_argument("--all-logo-variants", action="store_true")
    candidate_p.set_defaults(func=lambda args: command_candidate(args, preview=False))

    promote_p = sub.add_parser("promote")
    promote_p.add_argument("--project", required=True)
    promote_p.add_argument("--render-dir")
    promote_p.add_argument("--approve-manual-qa", action="store_true")
    promote_p.set_defaults(func=command_promote)
    return parser


def main() -> int:
    load_env_file()
    args = build_parser().parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
