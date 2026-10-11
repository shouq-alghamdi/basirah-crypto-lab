# Security and private data

- Never commit Telegram tokens, chat IDs, exchange credentials, database files, logs or `.env` files.
- `setup.py` stores the Telegram settings locally with 0600 file permissions inside a 0700 directory. This is access restriction, not encryption.
- Do not publish screenshots showing credentials or private account information.
- Revoke any exposed Telegram token through BotFather; removing a commit does not revoke a token.
- Do not enable exchange withdrawals or real trading for this educational release.
- Keep Docker and Freqtrade maintained; review upgrades before changing the pinned version.

For a potential vulnerability, use GitHub's private reporting facility if enabled. Otherwise contact the repository owner privately. Never include credentials in a public issue.
