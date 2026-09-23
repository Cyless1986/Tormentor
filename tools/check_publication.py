"""Check the staged Git snapshot without printing credentials or private values."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = ['git', '-c', 'safe.directory=' + ROOT.as_posix()]


def main():
    names = subprocess.check_output(GIT + ['diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'], cwd=ROOT).decode().split('\0')
    failures = []
    count = 0
    total = 0
    blocked = {'.env', 'settings.json', 'connection.json', 'tablet-verbindung.json', 'tablet-verbindung.txt'}
    blocked_dirs = {'portal_lore', 'portal_handouts', 'portal_maps', 'loreify', 'logs', 'downloads', 'private_lore', 'desktop_reference'}
    blocked_suffixes = {'.db', '.sqlite', '.sqlite3', '.wav', '.mp3', '.mp4', '.apk', '.zip', '.jks', '.keystore', '.pem', '.key'}
    signatures = [
        ('private key', re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
        ('OpenAI key', re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}')),
        ('GitHub token', re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})')),
        ('Google key', re.compile(rb'\bAIza[A-Za-z0-9_-]{30,}')),
        ('AWS key', re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ]
    private_values = []
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.partition('=')
            value = value.strip().strip('\"\'')
            if sep and len(value) >= 12 and not key.lstrip().startswith('#'):
                private_values.append(value.encode())
    for name in filter(None, names):
        path = Path(name)
        if path.name.lower() in blocked or set(path.parts) & blocked_dirs or path.suffix.lower() in blocked_suffixes:
            failures.append((name, 'private data or binary artifact path'))
        content = subprocess.check_output(GIT + ['show', ':' + name], cwd=ROOT)
        count += 1
        total += len(content)
        if len(content) > 10 * 1024 * 1024:
            failures.append((name, 'file exceeds source publication limit'))
        for label, pattern in signatures:
            if pattern.search(content):
                failures.append((name, label))
        if any(value in content for value in private_values):
            failures.append((name, 'contains a local secret value'))
    if failures:
        for name, reason in failures:
            print(name + ': ' + reason)
        raise SystemExit('Publication check failed; no secret values printed.')
    print(f'Publication check passed: {count} staged files, {total:,} bytes; no blocked paths or detected secrets.')


if __name__ == '__main__':
    main()
