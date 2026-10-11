"""Create local-only Telegram configuration; no credentials in source control."""
import getpass
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def main():
    os.umask(0o077)
    folder = ROOT / 'private'
    folder.mkdir(mode=0o700, exist_ok=True)
    folder.chmod(0o700)
    target = folder / 'telegram.json'
    if target.exists():
        print('Local settings already exist; preserved without changes.')
        return
    print('Optional Telegram alerts. Leave the token blank to run without Telegram.')
    token = getpass.getpass('Bot token (hidden): ').strip()
    telegram = {'enabled': False}
    if token:
        chat = input('Your private chat ID: ').strip()
        if not re.fullmatch(r'\d+:[A-Za-z0-9_-]+', token) or not re.fullmatch(r'\d+', chat):
            raise SystemExit('Invalid token or private chat ID format. Nothing saved.')
        telegram = {'enabled': True, 'token': token, 'chat_id': chat}
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump({'telegram': telegram}, handle)
    (ROOT / 'user_data/logs').mkdir(parents=True, exist_ok=True)
    print('Local configuration saved. Run docker compose up -d to start paper trading.')

if __name__ == '__main__':
    main()
