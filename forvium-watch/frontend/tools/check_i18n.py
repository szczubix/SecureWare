"""Kontrola tlumaczen paneli (CI): python3 tools/check_i18n.py

* kazdy tekst tr("...") i tekst statyczny HTML ma tlumaczenie w tools/en.py,
* w kodzie nie zostal polski tekst poza tr(...) (poza komentarzami),
* tlumaczenia maja te same parametry {...},
* shared/i18n-en.js jest wygenerowany z aktualnego tools/en.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from en import EN  # noqa: E402

POLISH = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\]|\\.)*)`')
# Klucze widokow panelu klienta (tlumaczone przez tr(label) w nawigacji).
NAV_KEYS = ["Dashboard", "Jednostki", "Technologie", "CVE", "Diagnostyka", "Zgłoszenia", "Członkowie", "Konto",
            "Dostęp serwisowy", "Powiadomienia"]


def strip_comments(src: str) -> str:
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1]); i = j + 1
        elif src.startswith("//", i) and (i == 0 or src[i - 1] != ":"):
            j = src.find("\n", i); i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i); i = n if j < 0 else j + 2
        else:
            out.append(c); i += 1
    return "".join(out)


def main() -> int:
    errors, keys = [], list(NAV_KEYS)
    files = sorted([*ROOT.glob("app/*.js"), *ROOT.glob("admin/*.js")])
    for f in files:
        src = strip_comments(f.read_text(encoding="utf-8"))
        keys += [json.loads(f'"{m}"') for m in re.findall(r'\btr\("((?:[^"\\]|\\.)*)"', src)]
        for m in STRING.finditer(src):
            text = m.group(1) if m.group(1) is not None else m.group(2)
            translated = src[max(0, m.start() - 3):m.start()].endswith("tr(")
            nav_key = src[m.start() - 1] == "[" and src[m.end():m.end() + 1] == "]" and text in NAV_KEYS
            if POLISH.search(text) and not translated and not nav_key:
                line = src.count("\n", 0, m.start()) + 1
                errors.append(f"{f.relative_to(ROOT)}:{line}: tekst bez tr(): {text[:80]!r}")
    for f in sorted([*ROOT.glob("app/*.html"), *ROOT.glob("admin/*.html")]):
        html = f.read_text(encoding="utf-8")
        keys += [m.strip() for m in re.findall(r"<title>([^<]+)</title>|data-i18n>([^<]+)<", html) for m in m if m]
    for k in dict.fromkeys(keys):
        if k not in EN:
            errors.append(f"brak tlumaczenia w tools/en.py: {k!r}")
    fields = lambda s: sorted(re.findall(r"\{(\w+)\}", s))  # noqa: E731
    for pl, en in EN.items():
        if fields(pl) != fields(en):
            errors.append(f"inne parametry: {pl!r} -> {en!r}")
        if POLISH.search(en):
            errors.append(f"polskie znaki w tlumaczeniu: {en!r}")
    generated = (ROOT / "shared" / "i18n-en.js").read_text(encoding="utf-8")
    if json.loads(generated.split("=", 1)[1].rstrip().rstrip(";")) != EN:
        errors.append("shared/i18n-en.js nieaktualny - uruchom: python3 tools/en.py > shared/i18n-en.js")
    print("\n".join(errors) or f"OK: {len(dict.fromkeys(keys))} tekstow, {len(EN)} tlumaczen")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
