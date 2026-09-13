#!/usr/bin/env python3
"""Store or delete a Telegram secret without echoing it to the terminal."""
from __future__ import annotations

import argparse
import getpass

import keyring

SERVICE = "codex-telegram-plugin"
ALLOWED = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Telegram credentials in the operating-system credential store.")
    parser.add_argument("name", nargs="?", default="TELEGRAM_BOT_TOKEN", choices=ALLOWED)
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()
    if args.delete:
        try:
            keyring.delete_password(SERVICE, args.name)
        except keyring.errors.PasswordDeleteError:
            pass
        print(f"Deleted {args.name} from Windows Credential Manager.")
        return
    value = getpass.getpass(f"Enter {args.name} (input hidden): ").strip()
    if not value:
        raise SystemExit("No value entered; credential was not changed.")
    keyring.set_password(SERVICE, args.name, value)
    print(f"Stored {args.name} in Windows Credential Manager.")


if __name__ == "__main__":
    main()
