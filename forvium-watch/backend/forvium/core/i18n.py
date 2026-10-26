"""Tlumaczenia tekstow widocznych dla uzytkownika (pl - jezyk zrodlowy, en).

Tekst zrodlowy jest po polsku i sluzy jako klucz katalogu (forvium/locales/en.py), wiec kod
czyta sie jak dotad. Teksty z parametrami tworzy sie przez `L(...)`:

    L("Nie znaleziono {what}.", what=...)        # szablon + parametry, tlumaczony przy wyswietleniu

Jezyk:
* odpowiedz API (komunikaty bledow, tekst banera) - naglowek Accept-Language zadania
  (frontend wysyla wybrany jezyk); bez naglowka - FORVIUM_DEFAULT_LOCALE,
* powiadomienia i e-maile - jezyk odbiorcy (users.locale, potem organizations.locale),
* raport PDF klienta - jezyk organizacji.

Test tests/test_i18n.py sprawdza, ze kazdy polski tekst w kodzie ma tlumaczenie.
"""

from __future__ import annotations

import os
import re
from contextvars import ContextVar
from functools import lru_cache

LANGS = ("pl", "en")
SOURCE = "pl"

_request_lang: ContextVar[str | None] = ContextVar("forvium_lang", default=None)


def default_lang() -> str:
    lang = os.environ.get("FORVIUM_DEFAULT_LOCALE", SOURCE)
    return lang if lang in LANGS else SOURCE


def normalize(lang: str | None) -> str | None:
    lang = (lang or "").strip().lower()[:2]
    return lang if lang in LANGS else None


def negotiate(accept_language: str | None) -> str:
    """Pierwszy obslugiwany jezyk z naglowka Accept-Language (kolejnosc wg wag q)."""
    best, best_q = None, -1.0
    for i, part in enumerate((accept_language or "").split(",")):
        tag, _, params = part.strip().partition(";")
        lang = normalize(tag)
        if lang is None:
            continue
        q = 1.0
        m = re.search(r"q=([0-9.]+)", params)
        if m:
            try:
                q = float(m.group(1))
            except ValueError:
                q = 0.0
        if q > best_q:
            best, best_q = lang, q
    return best or default_lang()


def current_lang() -> str:
    return _request_lang.get() or default_lang()


def set_request_lang(lang: str | None):
    return _request_lang.set(lang)


def reset_request_lang(token) -> None:
    _request_lang.reset(token)


@lru_cache(maxsize=None)
def catalog(lang: str) -> dict[str, str]:
    if lang == "en":
        from forvium.locales.en import EN

        return EN
    return {}


class L:
    """Tekst do przetlumaczenia: polski szablon + parametry (wartosci moga byc tez `L`)."""

    __slots__ = ("template", "params")

    def __init__(self, template: str, **params) -> None:
        self.template = template
        self.params = params

    def render(self, lang: str | None = None) -> str:
        lang = lang or current_lang()
        template = catalog(lang).get(self.template, self.template)
        if not self.params:
            return template
        return template.format(**{k: tr(v, lang) for k, v in self.params.items()})

    def __str__(self) -> str:
        return self.render(SOURCE)

    def __repr__(self) -> str:
        return f"L({self.template!r}, **{self.params!r})"

    def __add__(self, other) -> Joined:
        return Joined("", [self, other])

    def __radd__(self, other) -> Joined:
        return Joined("", [other, self])

    def __eq__(self, other) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


class Joined(L):
    """Polaczenie tekstow (np. tresc powiadomienia skladana z czesci)."""

    __slots__ = ("sep", "parts")

    def __init__(self, sep: str, parts) -> None:
        super().__init__("")
        self.sep = sep
        self.parts = list(parts)

    def render(self, lang: str | None = None) -> str:
        lang = lang or current_lang()
        return tr(self.sep, lang).join(tr(p, lang) for p in self.parts)

    def __add__(self, other) -> Joined:
        return Joined("", [*self.parts, other]) if self.sep == "" else Joined("", [self, other])

    def __repr__(self) -> str:
        return f"Joined({self.sep!r}, {self.parts!r})"


def join(sep: str, parts) -> Joined:
    return Joined(sep, parts)


def tr(text, lang: str | None = None) -> str:
    """Tlumaczy `L`, tekst zrodlowy z katalogu albo zostawia inne wartosci bez zmian."""
    lang = lang or current_lang()
    if isinstance(text, L):
        return text.render(lang)
    if not isinstance(text, str):
        return "" if text is None else str(text)
    return catalog(lang).get(text, text)


# ------------------------------------------------------- teksty zapisane w bazie
@lru_cache(maxsize=None)
def _patterns(lang: str) -> list[tuple[re.Pattern, str]]:
    out = []
    for source, target in catalog(lang).items():
        if "{" not in source:
            continue
        regex, pos = "", 0
        for m in re.finditer(r"\{(\w+)\}", source):
            regex += re.escape(source[pos:m.start()]) + f"(?P<{m.group(1)}>.+?)"
            pos = m.end()
        regex += re.escape(source[pos:])
        try:
            out.append((re.compile(f"^{regex}$", re.S), target))
        except re.error:  # ten sam parametr dwa razy - pomijamy
            continue
    return out


def tr_stored(text: str | None, lang: str | None = None) -> str | None:
    """Tlumaczy tekst zapisany w bazie po polsku (np. tytul alertu, notatka decyzji)."""
    lang = lang or current_lang()
    if not text or lang == SOURCE:
        return text
    exact = catalog(lang).get(text)
    if exact is not None:
        return exact
    for regex, target in _patterns(lang):
        m = regex.match(text)
        if m:
            return target.format(**{k: tr(v, lang) for k, v in m.groupdict().items()})
    return text


def lang_from_scope(scope) -> str:
    for name, value in scope.get("headers") or ():
        if name == b"accept-language":
            return negotiate(value.decode("latin-1"))
    return default_lang()


class LanguageMiddleware:
    """Ustawia jezyk zadania (Accept-Language) dla komunikatow API."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        token = set_request_lang(lang_from_scope(scope))
        try:
            await self.app(scope, receive, send)
        finally:
            reset_request_lang(token)
