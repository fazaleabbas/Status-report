"""
analyse_projects.py
-------------------
Enriches raw project inputs (name + status) using a local Ollama LLM before
the PowerPoint deck is built.

Enrichment adds:
  - polished executive-ready status text
  - RAG colour (green / amber / red)
  - progress label (short phrase shown on the card chip)
  - next_step (one clear action sentence)
  - notes (two concise bullet points)
  - portfolio_summary (one paragraph across all projects)

If Ollama is not running or the model is unavailable the module falls back to
a deterministic rule-based enrichment so the program never crashes.

Recommended local model: llama3.2  (fast, fits in 8 GB RAM)
Install:
    brew install ollama
    ollama pull llama3.2
    ollama serve          # keep running in the background
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default model – can be overridden by the caller
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "llama3.2"

# ---------------------------------------------------------------------------
# Rule-based fallback helpers (identical logic to generate_status_report.py)
# ---------------------------------------------------------------------------
_RED_KEYWORDS = [
    "risk", "blocked", "blocker", "delay", "issue",
    "pending", "removed", "security", "failed", "critical",
]
_GREEN_KEYWORDS = [
    "done", "complete", "completed", "on track",
    "certified", "shipped", "successful",
]
_PROGRESS_HINTS = [
    ("complete", "Complete"),
    ("complet", "Completed"),
    ("testing", "Testing"),
    ("certif", "Certification"),
    ("discovery", "Discovery"),
    ("planning", "Planning"),
    ("poc", "POC"),
    ("review", "Under Review"),
    ("shipped", "Shipped"),
    ("deploy", "Deployment"),
    ("develop", "Development"),
]


def _rule_based_rag(status: str) -> str:
    text = status.lower()
    if any(k in text for k in _RED_KEYWORDS):
        return "red"
    if any(k in text for k in _GREEN_KEYWORDS):
        return "green"
    return "amber"


def _rule_based_progress(status: str) -> str:
    text = status.lower()
    for hint, label in _PROGRESS_HINTS:
        if hint in text:
            return label
    return "In Progress"


def _rule_based_enrich_one(project: dict[str, str]) -> dict[str, Any]:
    name = project["name"]
    raw_status = project["status"]
    explicit_rag = project.get("rag", "")

    rag = explicit_rag if explicit_rag in {"green", "amber", "red"} else _rule_based_rag(raw_status)
    progress = _rule_based_progress(raw_status)

    rag_labels = {"green": "On Track", "amber": "In Progress", "red": "At Risk"}
    next_step = f"Confirm the next milestone and owner for {name}."
    notes = [
        f"{name} status has been captured from the latest project update.",
        f"Current position: {rag_labels[rag]}. Review in the next reporting cycle.",
    ]

    return {
        "name": name,
        "rag": rag,
        "progress": progress,
        "status": raw_status,
        "next_step": next_step,
        "notes": notes,
    }


def _rule_based_portfolio_summary(projects: list[dict[str, Any]]) -> str:
    green = sum(1 for p in projects if p["rag"] == "green")
    amber = sum(1 for p in projects if p["rag"] == "amber")
    red = sum(1 for p in projects if p["rag"] == "red")
    parts = []
    if green:
        parts.append(f"{green} initiative{'s' if green > 1 else ''} on track")
    if amber:
        parts.append(f"{amber} progressing with dependencies")
    if red:
        parts.append(f"{red} requiring immediate attention")
    body = ", ".join(parts) if parts else "all initiatives under review"
    return f"Portfolio update: {body}. Full details are provided in the slides below."


# ---------------------------------------------------------------------------
# LLM prompt + JSON extraction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an expert PMO analyst who writes concise, executive-level project "
    "status reports. You always reply with valid JSON only — no markdown fences, "
    "no extra commentary."
)

_PROJECT_PROMPT_TEMPLATE = """
Analyse the following project update and return a JSON object with these exact keys:

  "rag"         : one of "green", "amber", or "red"
                  green = on track / complete
                  amber = in progress but has dependencies or is awaiting action
                  red   = blocked / at risk / removed / security issue
  "progress"    : a short label (2-4 words) summarising where the project is right now
                  examples: "80% Complete", "Discovery Stage", "Certification Prep",
                             "Cards Shipped", "POC Planning", "Pending Review"
  "status"      : a single polished executive-ready sentence (max 30 words) that
                  summarises the current state clearly
  "next_step"   : one clear, actionable sentence describing what must happen next
  "notes"       : an array of exactly 2 short bullet-point strings (no bullet character)
                  each highlighting a key consideration or dependency

Project name: {name}
Raw status update: {status}

Respond with the JSON object only.
""".strip()

_PORTFOLIO_PROMPT_TEMPLATE = """
You are writing the executive summary paragraph for a project status report.
Given the following project list (name and RAG), write a single concise paragraph
(max 40 words) that describes the overall portfolio health for a senior audience.

Projects:
{project_list}

Respond with the paragraph text only — no JSON, no bullet points.
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response.")
    return json.loads(match.group())


def _call_ollama(prompt: str, model: str, system: str = _SYSTEM_PROMPT) -> str:
    """Call the local Ollama HTTP API and return the response text."""
    import urllib.request

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    return result["message"]["content"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enrich_projects(
    simple_projects: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    on_progress: Any = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Enrich a list of raw projects using a local Ollama LLM.

    Parameters
    ----------
    simple_projects : list of dicts with keys 'name', 'status', and optionally 'rag'
    model           : Ollama model name (default: llama3.2)
    on_progress     : optional callable(current: int, total: int, message: str)
                      called after each project is processed so the UI can update

    Returns
    -------
    (enriched_projects, portfolio_summary)
    """
    total = len(simple_projects)
    enriched: list[dict[str, Any]] = []
    used_llm = False

    for idx, project in enumerate(simple_projects):
        name = project["name"]
        if on_progress:
            on_progress(idx, total, f"Analysing {name}…")

        # If the user provided an explicit RAG, keep it but still enrich the rest
        explicit_rag = project.get("rag", "")

        try:
            prompt = _PROJECT_PROMPT_TEMPLATE.format(
                name=name, status=project["status"]
            )
            raw = _call_ollama(prompt, model)
            result = _extract_json(raw)

            rag = explicit_rag if explicit_rag in {"green", "amber", "red"} else str(result.get("rag", "amber")).lower()
            if rag not in {"green", "amber", "red"}:
                rag = "amber"

            notes_raw = result.get("notes", [])
            notes = [str(n) for n in notes_raw[:2]] if isinstance(notes_raw, list) else []
            while len(notes) < 2:
                notes.append(f"Review {name} in the next reporting cycle.")

            enriched.append({
                "name": name,
                "rag": rag,
                "progress": str(result.get("progress", "In Progress")).strip(),
                "status": str(result.get("status", project["status"])).strip(),
                "next_step": str(result.get("next_step", f"Confirm next milestone for {name}.")).strip(),
                "notes": notes,
            })
            used_llm = True

        except Exception as exc:
            logger.warning("Ollama enrichment failed for '%s': %s — using rule-based fallback.", name, exc)
            enriched.append(_rule_based_enrich_one(project))

    if on_progress:
        on_progress(total, total, "Generating portfolio summary…")

    # Portfolio summary
    portfolio_summary = ""
    if used_llm and enriched:
        try:
            project_list = "\n".join(
                f"- {p['name']}: {p['rag'].upper()} — {p['status']}" for p in enriched
            )
            portfolio_summary = _call_ollama(
                _PORTFOLIO_PROMPT_TEMPLATE.format(project_list=project_list),
                model,
                system="You are a senior PMO analyst. Reply with plain text only.",
            ).strip()
        except Exception as exc:
            logger.warning("Portfolio summary LLM call failed: %s", exc)

    if not portfolio_summary:
        portfolio_summary = _rule_based_portfolio_summary(enriched)

    if on_progress:
        on_progress(total, total, "Analysis complete.")

    return enriched, portfolio_summary


def check_ollama_available(model: str = DEFAULT_MODEL) -> tuple[bool, str]:
    """
    Quick health-check for Ollama.

    Returns (is_available: bool, message: str)
    """
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
            data = json.loads(resp.read().decode())
        available_models = [m["name"] for m in data.get("models", [])]
        base_names = [m.split(":")[0] for m in available_models]
        if model in available_models or model in base_names:
            return True, f"Ollama is running. Model '{model}' is available."
        if available_models:
            return False, (
                f"Ollama is running but model '{model}' is not pulled.\n"
                f"Available: {', '.join(available_models)}\n"
                f"Run:  ollama pull {model}"
            )
        return False, f"Ollama is running but no models are pulled. Run:  ollama pull {model}"
    except Exception as exc:
        return False, (
            f"Ollama is not reachable ({exc}).\n"
            "Install: brew install ollama\n"
            f"Then:    ollama pull {model} && ollama serve"
        )

