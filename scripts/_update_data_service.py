#!/usr/bin/env python3
"""
One-off update script: add the `data-service` achievement bullet to the Delta Labs
role of every applications/*/tailored.yaml, without disturbing JD-specific tailoring.

Idempotent — skips files that already mention "data-service" or "data service".
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPS = ROOT / "applications"

BULLET = (
    'Architected and shipped a greenfield FastAPI microservice (data-service) '
    'from scratch, replacing the legacy distribution model with a significantly '
    'more efficient design — weighted distributions, multi-country support, '
    'reference validation.'
)


def add_bullet(text: str) -> tuple[str, bool]:
    """Insert one new bullet at the end of Delta Labs's bullets list (before its stack line).
    Returns (new_text, changed)."""
    if "data-service" in text or "data service" in text.lower():
        return text, False

    lines = text.split("\n")
    out = []
    in_delta = False
    in_bullets = False
    bullet_indent = None
    inserted = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect Delta Labs experience entry
        if re.match(r'\s+(?:- )?company:\s*"Delta Labs', line):
            in_delta = True
            in_bullets = False
        elif re.match(r'\s+(?:- )?company:\s*"', line) and in_delta:
            in_delta = False
            in_bullets = False

        if in_delta:
            # Detect entering bullets list
            if re.match(r'\s+bullets:\s*$', line):
                in_bullets = True
                # Find indent for bullet items by looking at next non-blank line
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("-"):
                        bullet_indent = len(lines[j]) - len(lines[j].lstrip())
                        break

            # When we hit `stack:` (or end of bullets), insert the new bullet right before it
            if in_bullets and not inserted:
                # any non-bullet, non-blank line ending the bullets list:
                if (
                    re.match(r'\s+stack:', line)
                    or re.match(r'\s+(?:- )?company:\s*"', line)
                    or re.match(r'\s+blurb:', line)
                ):
                    if bullet_indent is None:
                        bullet_indent = 6  # safe default for `    - ` under `  - bullets:`
                    indent = " " * bullet_indent
                    new_line = f'{indent}- "{BULLET}"'
                    out.append(new_line)
                    inserted = True
                    in_bullets = False

        out.append(line)

    if inserted:
        return "\n".join(out), True
    return text, False


def main():
    changed = 0
    skipped = 0
    for app_dir in sorted(APPS.iterdir()):
        if not app_dir.is_dir():
            continue
        path = app_dir / "tailored.yaml"
        if not path.exists():
            continue
        text = path.read_text()
        new, did = add_bullet(text)
        if did:
            path.write_text(new)
            print(f"  + {app_dir.name}")
            changed += 1
        else:
            print(f"  · skip (already present): {app_dir.name}")
            skipped += 1
    print(f"\nupdated {changed}, skipped {skipped}")


if __name__ == "__main__":
    main()
