"""Reusable prompt builder for Gemini."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_PROMPT_PATH = Path("System+Prompt+2ac0c4613418808c8d6dd8e9f9c2059c.md")
FALLBACK_PROMPT = "You rate doodles for a deterministic battle demo. Output JSON per the schema."

DIVERSITY_GUIDANCE = (
    "### Diversity Rules\n"
    "- Base every choice on the player's latest doodle plus the metadata below. "
    "Reference what you see in the stroke summary when you justify decisions.\n"
    "- Choose the element that best matches the doodle's strokes and shapes; "
    "do not default to a single element. If multiple elements seem equally valid, lean toward the suggested variety target (if present).\n"
    "- Vary health/attack/defense distributions (or power adjustments) within allowed ranges so results feel distinct yet grounded in the drawing.\n"
    "- Variety guidance is secondary: if the stroke traits clearly indicate a specific element or stat profile, honor the doodle first.\n"
    "- Give every name/move_name a fresh quirky spin tied to the doodle. Reusing previous wording is discouraged.\n"
)

SCHEMA_MARKERS: Dict[str, List[str]] = {
    "Monster": ["### **Monster Schema**", "### Monster constraints"],
    "Skill": ["### **Skill Schema**", "### Skill constraints"],
    "Monster_Enhance": ["### **Monster_Enhance Schema**", "### Enhancement constraints"],
    "Skill_Enhance": ["### **Skill_Enhance Schema**", "### Enhancement constraints"],
}

COMMON_SECTION_MARKERS: List[str] = [
    "## 2. Stroke interpretation guidance",
    "## 3. Validation constraints",
    "### Elements & advantage cycle",
    "## 4. Tone of explanations",
]


@lru_cache
def _load_base_prompt() -> str:
    custom_path = os.getenv("GEMINI_PROMPT_PATH")
    candidate_paths: List[Path] = []
    if custom_path:
        candidate_paths.append(Path(custom_path))
    candidate_paths.append(DEFAULT_PROMPT_PATH)

    for path in candidate_paths:
        if path.is_absolute() and path.exists():
            return path.read_text(encoding="utf-8")
        if not path.is_absolute():
            repo_path = Path(__file__).resolve().parents[2] / path
            if repo_path.exists():
                return repo_path.read_text(encoding="utf-8")
    return FALLBACK_PROMPT


def _extract_section(text: str, marker: str) -> str:
    """Return text under the heading that matches marker."""
    lines = text.splitlines()
    capture = False
    results: List[str] = []
    target = marker.strip()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(target):
            capture = True
            results.append(line)
            continue
        if capture and (stripped.startswith("### ") or stripped.startswith("## ") or stripped.startswith("# ")):
            if not stripped.startswith(target):
                break
        if capture:
            results.append(line)
    return "\n".join(results).strip()


def _schema_sections(base_prompt: str, schema_hint: str) -> str:
    sections: List[str] = []
    for marker in SCHEMA_MARKERS.get(schema_hint, []):
        section = _extract_section(base_prompt, marker)
        if section:
            sections.append(section)
    return "\n\n".join(sections).strip()


def _common_sections(base_prompt: str) -> str:
    sections: List[str] = []
    for marker in COMMON_SECTION_MARKERS:
        section = _extract_section(base_prompt, marker)
        if section:
            sections.append(section)
    return "\n\n".join(sections).strip()


def build_prompt(
    schema_hint: str,
    strokes: List[Dict[str, Any]],
    seed: int,
    metadata: Dict[str, Any],
    snapshot_hint: str | None = None,
) -> str:
    base = _load_base_prompt()
    summary = _summarize_strokes(strokes)
    schema_block = _schema_sections(base, schema_hint) or "Follow the expected JSON schema."
    common_block = _common_sections(base)
    metadata = metadata or {}
    metadata_copy = dict(metadata)
    hints = metadata_copy.pop("_hints", {})
    metadata_text = json.dumps(metadata_copy, ensure_ascii=False)
    hints_block = _format_hints(hints)
    prompt_parts = [schema_block]
    if common_block:
        prompt_parts.append(common_block)
    prompt_parts.append(DIVERSITY_GUIDANCE)
    context_lines: List[str] = [
        f"Schema: {schema_hint}",
        f"Seed: {seed}",
        f"Metadata: {metadata_text}",
    ]
    if snapshot_hint:
        context_lines.append(f"Snapshot Preview: {snapshot_hint}")
    if hints_block:
        context_lines.append(hints_block)
    context_lines.append(f"Stroke Summary: {summary}")
    prompt_parts.append(
        "### Current Doodle Context\n"
        + "\n".join(context_lines)
        + "\n\nRespond with JSON that matches the schema exactly. DO NOT wrap the payload "
        "inside additional objects (no root keys like “monster” or “skill”). "
        "Do not include extra narrative fields."
    )
    return "\n\n".join(prompt_parts)


def _format_hints(hints: Dict[str, Any]) -> str:
    if not hints:
        return ""
    parts: List[str] = []
    recent = hints.get("recent_results")
    if recent:
        parts.append(f"Recent Outputs: {json.dumps(recent, ensure_ascii=False)}")
    traits = hints.get("stroke_traits")
    if traits:
        parts.append(f"Stroke Traits: {json.dumps(traits, ensure_ascii=False)}")
    variety = hints.get("variety_target")
    if variety:
        parts.append(f"Variety Target: aim for element '{variety}' if it fits the doodle.")
    return "\n".join(parts)


def _summarize_strokes(strokes: List[Dict[str, Any]]) -> str:
    sample = strokes[:20]
    try:
        return json.dumps(sample, ensure_ascii=False)
    except TypeError:
        return str(sample)
