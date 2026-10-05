#!/usr/bin/env python3
"""Validate this skill's local structure; never render or claim semantic accuracy.

Python 3.10+, standard library only. Read-only; no network or subprocess calls.
This checks a small documented metadata subset, not the full YAML language.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

REQUIRED = (
    'SKILL.md', 'README.md', 'CHANGELOG.md', 'VALIDATION.md',
    'agents/openai.yaml', 'references/prompt-playbook.md',
    'references/continuity-and-causality.md', 'references/model-logic.md',
    'references/provider-checks.md', 'references/quality-and-iteration.md',
    'references/examples.md', 'references/sources.md',
    'references/behavioral-tests.md', 'assets/job-template.md',
    'assets/context-handoff.md', 'assets/continuity-ledger.md',
    'assets/prompt-template.md', 'assets/review-record.md',
    'evals/evals.json', 'evals/README.md',
    'evals/test_validate_bundle.py', 'docs/seedance-2-5-agent-guide.md',
    'scripts/validate_bundle.py',
)
MAX_BYTES = 25 * 1024 * 1024
LINK = re.compile(r'\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')


def package_files(root: Path) -> list[Path]:
    """Ignore Python runtime caches, which must not be distributed."""
    return sorted(p for p in root.rglob('*') if p.is_file()
                  and '__pycache__' not in p.parts and p.suffix != '.pyc')


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in package_files(root) if p.relative_to(root).as_posix() != 'manifest.json'}


def prose(text: str) -> tuple[str, bool]:
    """Remove fenced code so examples are not mistaken for live Markdown links."""
    lines: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        m = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if m:
            marker = m.group(1)
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return '\n'.join(lines), fence is None


def slug(value: str) -> str:
    value = re.sub(r'<[^>]+>', '', value).strip().lower()
    return re.sub(r'[^\w\s-]', '', value).replace(' ', '-')


def anchor_ids(text: str) -> set[str]:
    clean, _ = prose(text)
    explicit = set(re.findall(r'<a\s+id=["\']([^"\']+)["\']', clean))
    counts: dict[str, int] = {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', clean, re.M):
        base = slug(heading)
        n = counts.get(base, 0)
        explicit.add(base if n == 0 else f'{base}-{n}')
        counts[base] = n + 1
    return explicit


def validate(root: Path, check_integrity: bool = False) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        return [f'Not a package directory: {root}']
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f'Missing required file: {rel}')
    for p in root.rglob('*'):
        if p.is_symlink():
            errors.append(f'Symlink not allowed: {p.relative_to(root)}')
    if errors:
        return errors
    paths = package_files(root)
    if sum(p.stat().st_size for p in paths) > MAX_BYTES:
        errors.append('Uncompressed package exceeds 25 MB')
    entries = [p for p in paths if p.name == 'SKILL.md']
    if entries != [root / 'SKILL.md']:
        errors.append('Expected exactly one root SKILL.md entrypoint')
    entry = (root / 'SKILL.md').read_text(encoding='utf-8')
    fm = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', entry, re.S)
    if not fm:
        errors.append('Missing YAML frontmatter delimiters')
    else:
        keys = re.findall(r'^([A-Za-z_][\w-]*):', fm.group(1), re.M)
        if sorted(keys) != ['description', 'name']:
            errors.append('Frontmatter must contain only name and description')
        if not re.search(r'^name: seedance-2-5-director\s*$', fm.group(1), re.M):
            errors.append('Unexpected skill name')
    if len(entry.splitlines()) >= 500:
        errors.append('Entrypoint must stay below 500 lines')
    meta = (root / 'agents/openai.yaml').read_text(encoding='utf-8')
    for key in ('interface:', 'display_name:', 'short_description:'):
        if key not in meta:
            errors.append(f'Missing metadata field: {key}')
    for p in paths:
        if p.suffix != '.md':
            continue
        text = p.read_text(encoding='utf-8')
        clean, closed = prose(text)
        rel = p.relative_to(root).as_posix()
        if not closed:
            errors.append(f'Unclosed code fence: {rel}')
        for target in LINK.findall(clean):
            u = urlsplit(target)
            if u.scheme or u.netloc:
                continue  # External availability is intentionally not tested.
            dest = (p.parent / unquote(u.path)).resolve() if u.path else p
            if not dest.is_relative_to(root):
                errors.append(f'Link escapes package: {rel} -> {target}')
            elif not dest.is_file():
                errors.append(f'Broken local link: {rel} -> {target}')
            elif u.fragment and dest.suffix == '.md':
                if unquote(u.fragment) not in anchor_ids(dest.read_text(encoding='utf-8')):
                    errors.append(f'Broken anchor: {rel} -> {target}')
    try:
        fixture = json.loads((root / 'evals/evals.json').read_text(encoding='utf-8'))
        cases = fixture.get('cases')
        if not isinstance(cases, list) or not cases:
            errors.append('Evaluation cases must be a nonempty list')
        else:
            seen: set[str] = set()
            for index, c in enumerate(cases):
                if not isinstance(c, dict):
                    errors.append(f'Invalid case object: {index}')
                    continue
                ident = c.get('id')
                if not isinstance(ident, str) or not ident or ident in seen:
                    errors.append(f'Invalid or duplicate case ID: {ident}')
                elif isinstance(ident, str):
                    seen.add(ident)
                if not isinstance(c.get('prompt'), str) or not c['prompt'].strip():
                    errors.append(f'Missing case prompt: {ident}')
                expected = c.get('expected_behaviors')
                if not isinstance(expected, list) or not expected or not all(isinstance(x, str) and x.strip() for x in expected):
                    errors.append(f'Invalid expected behaviors: {ident}')
                turns = c.get('conversation', [])
                if not isinstance(turns, list):
                    errors.append(f'Invalid conversation: {ident}')
                else:
                    for turn in turns:
                        if not isinstance(turn, dict) or turn.get('role') not in {'user', 'assistant', 'system'} or not isinstance(turn.get('content'), str):
                            errors.append(f'Invalid conversation message: {ident}')
    except (json.JSONDecodeError, AttributeError) as exc:
        errors.append(f'Invalid evaluation JSON: {exc}')
    if check_integrity:
        try:
            manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
            recorded = manifest.get('files')
            actual = inventory(root)
            if not isinstance(recorded, dict):
                errors.append('Manifest files must be a hash mapping')
            else:
                for name in sorted(set(recorded) | set(actual)):
                    if recorded.get(name) != actual.get(name):
                        errors.append(f'Integrity mismatch: {name}')
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f'Invalid or missing manifest: {exc}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--integrity', action='store_true', help='Also compare every file against manifest.json')
    args = parser.parse_args()
    try:
        errors = validate(args.root, args.integrity)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f'FAIL: cannot inspect package: {exc}')
        return 1
    if errors:
        for error in errors:
            print(f'FAIL: {error}')
        return 1
    print('PASS: package structure' + (' and file hashes' if args.integrity else '') + '.')
    print('NOT TESTED: agent behavior, source freshness, physical accuracy, or rendered video.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
