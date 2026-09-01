#!/usr/bin/env python3
"""Validate every skills/*/SKILL.md in this repo.

A skill with malformed or missing frontmatter does not fail loudly — it silently
fails to load or fails to trigger, which looks like the model ignoring the user.
This catches that in CI instead.

Checks per skill:
  1. SKILL.md exists in the skill directory
  2. It opens with a YAML frontmatter block delimited by ---
  3. The block declares both `name` and `description`
  4. `name` equals the directory name (how the skill is invoked)
  5. `description` is non-empty and long enough to carry trigger phrases

Standard library only, per CLAUDE.md. Usage:
    python3 scripts/validate_skills.py [--skills-dir skills]

Exit code 0 = all valid, 1 = at least one problem, 2 = usage error.
"""
import argparse
import sys
from pathlib import Path

MIN_DESCRIPTION_CHARS = 40


def parse_frontmatter(text):
    """Return (mapping, error). Handles the single-level key: value frontmatter
    these skills use, including values folded across continuation lines."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing opening --- frontmatter delimiter on line 1"

    try:
        end = next(i for i, line in enumerate(lines[1:], start=1)
                   if line.strip() == "---")
    except StopIteration:
        return None, "frontmatter block is never closed with ---"

    fields, key = {}, None
    for line in lines[1:end]:
        if not line.strip():
            continue
        if not line[0].isspace() and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip()
        elif key is not None:
            fields[key] = f"{fields[key]} {line.strip()}".strip()
        else:
            return None, f"cannot parse frontmatter line: {line!r}"
    return fields, None


def validate_skill(skill_dir):
    """Validate one skill directory; return a list of problem strings.

    An empty list means the skill is well-formed. Every problem names the file
    and says why it matters, because these failures are silent at runtime: a
    skill with bad frontmatter does not error, it just never triggers.
    """
    problems = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return [f"{skill_dir.name}: no SKILL.md"]

    fields, error = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
    if error:
        return [f"{skill_dir.name}/SKILL.md: {error}"]

    name = fields.get("name")
    if not name:
        problems.append(f"{skill_dir.name}/SKILL.md: frontmatter has no `name`")
    elif name != skill_dir.name:
        problems.append(
            f"{skill_dir.name}/SKILL.md: frontmatter name {name!r} does not match "
            f"directory name {skill_dir.name!r} — the directory is how the skill "
            f"is invoked, so these must agree"
        )

    description = fields.get("description", "")
    if not description:
        problems.append(
            f"{skill_dir.name}/SKILL.md: frontmatter has no `description` — this is "
            f"what triggers the skill, so it must carry the trigger phrases"
        )
    elif len(description) < MIN_DESCRIPTION_CHARS:
        problems.append(
            f"{skill_dir.name}/SKILL.md: description is {len(description)} chars, "
            f"under the {MIN_DESCRIPTION_CHARS}-char minimum — too short to carry "
            f"the phrases a user would actually say"
        )

    return problems


def main():
    """CLI entry point: validate every skill directory and report the tally."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-dir", default="skills")
    args = parser.parse_args()

    skills_root = Path(args.skills_dir)
    if not skills_root.is_dir():
        print(f"No such directory: {skills_root}", file=sys.stderr)
        sys.exit(2)

    skill_dirs = sorted(d for d in skills_root.iterdir() if d.is_dir())
    if not skill_dirs:
        print(f"No skills found in {skills_root}", file=sys.stderr)
        sys.exit(2)

    problems = []
    for skill_dir in skill_dirs:
        found = validate_skill(skill_dir)
        problems.extend(found)
        print(f"{'FAIL' if found else 'ok  '}  {skill_dir.name}")

    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    print(f"\nAll {len(skill_dirs)} skills valid.")


if __name__ == "__main__":
    main()
