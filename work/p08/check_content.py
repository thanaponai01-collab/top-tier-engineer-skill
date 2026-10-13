from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

# Every verified loop handoff names its no-skill route near the handoff.
HANDOFFS = {
    "skills/build-discipline/SKILL.md",
    "skills/debug-protocol/SKILL.md",
    "skills/agent-release/SKILL.md",
    "skills/correctness-gate/SKILL.md",
    "skills/threat-model/SKILL.md",
    "skills/perf-optimize/SKILL.md",
    "skills/evolve-maintain/SKILL.md",
    "skills/safe-release/SKILL.md",
    "skills/project-foundation/SKILL.md",
}


def main():
    errors = []
    for name in sorted(HANDOFFS):
        text = (ROOT / name).read_text(encoding="utf-8")
        handoffs = list(re.finditer(r"(?:load|hand|to|through)\s+(?:the\s+)?(?:`verify-loop`|verify-loop)", text, re.I))
        if not handoffs:
            handoffs = list(re.finditer(r"verify-loop", text, re.I))[-1:]
        window = text[handoffs[-1].start():] if handoffs else ""
        if not handoffs or not re.search(r"fallback|unavailable|not installed|otherwise", window, re.I):
            errors.append(f"{name}: verify-loop handoff needs a nearby missing-skill fallback or limit")

    foundation = (ROOT / "skills/project-foundation/SKILL.md").read_text(encoding="utf-8")
    if "No other skill requires this one." in foundation:
        errors.append("project-foundation still claims no skill requires it")
    if not all(term.lower() in foundation.lower() for term in ("onboard-system", "drive", "this skill is absent")):
        errors.append("project-foundation must describe conditional callers and direct fallback")

    onboarding = (ROOT / "skills/onboard-system/SKILL.md").read_text(encoding="utf-8")
    if not all(term in onboarding for term in ("Otherwise inspect the same categories directly", "Without project-foundation installed")):
        errors.append("onboard-system must state its standalone route when project-foundation is missing")

    picker = (ROOT / "skills/pick-skill/SKILL.md").read_text(encoding="utf-8")
    if not all(term in picker for term in ("invocable on its own", "conditional handoff", "skill is missing")):
        errors.append("pick-skill must describe standalone use, conditional composition and missing-skill routing")

    linked_fallbacks = {
        "skills/drive/SKILL.md": ("calling step's stated fallback", "bounded work directly"),
        "skills/onboard-system/SKILL.md": ("Otherwise inspect the same categories directly", "Without project-foundation installed"),
        "skills/build-discipline/SKILL.md": ("If that reference is unavailable", "structural handoff check was unavailable"),
        "skills/evolve-maintain/SKILL.md": ("If the", "missing structural evidence"),
        "skills/project-setup/SKILL.md": ("If that reference is", "single-agent fallback"),
        "skills/drive-overnight/SKILL.md": ("If that reference is unavailable", "If `recall` is unavailable"),
        "skills/project-update/SKILL.md": ("If the reference is unavailable", "scaling rules could not be checked"),
        "skills/project-foundation/SKILL.md": ("If the project-context convention is unavailable", "do not create a separate index"),
        "skills/arch-design/SKILL.md": ("when available for next time", "does not depend on that skill"),
    }
    for name, phrases in linked_fallbacks.items():
        text = (ROOT / name).read_text(encoding="utf-8")
        if not all(phrase.lower() in text.lower() for phrase in phrases):
            errors.append(f"{name}: conditional skill/reference handoff needs its standalone route or missing-skill limit")

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"P08 content: {len(HANDOFFS)} verify-loop handoffs and {len(linked_fallbacks)} cross-skill/reference paths state their fallback or limit.")


if __name__ == "__main__":
    main()
