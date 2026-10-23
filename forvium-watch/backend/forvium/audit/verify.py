"""Weryfikacja lancucha skrotow: `python -m forvium.audit.verify plik.jsonl [--key KLUCZ]`."""

from __future__ import annotations

import argparse
import os
import sys

from forvium.audit.chain import verify_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--key", default=os.environ.get("FORVIUM_AUDIT_EXPORT_HMAC_KEY", ""),
                        help="klucz HMAC (domyślnie FORVIUM_AUDIT_EXPORT_HMAC_KEY)")
    args = parser.parse_args(argv)
    ok, count, message = verify_file(args.path, args.key.encode() or None)
    print(f"{'OK' if ok else 'BŁĄD'}: {message} (zweryfikowano {count} zdarzeń)")
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
