"""Sanityzacja zrzutow widoku (biala lista tagow i atrybutow).

Zrzut powstaje w przegladarce operatora, wiec traktujemy go jak dane
niezaufane: zostaja wylacznie znaczniki struktury i tekst. Usuwane sa
skrypty, style, obrazy, linki, obsluga zdarzen, wartosci pol formularzy i
wszystkie nieznane atrybuty. Wynik i tak jest wyswietlany klientowi w
iframe `sandbox` bez uprawnien do skryptow (obrona warstwowa).
"""

from __future__ import annotations

from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = {
    "div", "span", "p", "h1", "h2", "h3", "h4", "strong", "em", "b", "i", "small", "pre", "code",
    "table", "thead", "tbody", "tr", "th", "td", "ul", "ol", "li", "nav", "section", "header", "main",
    "label", "button", "details", "summary", "br", "hr", "input",
}
VOID_TAGS = {"br", "hr", "input"}
# Zawartosc tych elementow jest pomijana w calosci.
DROP_CONTENT = {"script", "style", "template", "iframe", "object", "embed", "svg", "math", "textarea",
                "select", "noscript", "title", "head"}
ALLOWED_ATTRS = {"class", "colspan", "rowspan", "hidden", "open", "disabled"}
INPUT_TYPES = {"checkbox", "radio"}
# Linki zachowuja tekst i klase, ale traca adres (zrzut nie moze nigdzie prowadzic).
RENAME = {"a": "span"}


class _Sanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.stack: list[str] = []
        # Stos tagow wewnatrz pomijanego elementu - konczymy pomijanie dopiero na
        # pasujacym znaczniku zamykajacym elementu z DROP_CONTENT.
        self.drop_stack: list[str] = []

    @property
    def drop_depth(self) -> int:
        return len(self.drop_stack)

    def handle_starttag(self, tag, attrs):
        tag = RENAME.get(tag, tag)
        if self.drop_stack or tag in DROP_CONTENT:
            if tag not in VOID_TAGS:
                self.drop_stack.append(tag)
            return
        if tag not in ALLOWED_TAGS:
            return
        clean = []
        attrs = dict(attrs)
        if tag == "input":
            if (attrs.get("type") or "").lower() not in INPUT_TYPES:
                return  # pola tekstowe (mogace zawierac dane wpisywane recznie) pomijamy
            clean.append(f'type="{escape(attrs["type"].lower())}"')
            if "checked" in attrs:
                clean.append("checked")
            clean.append("disabled")
        for name, value in attrs.items():
            name = name.lower()
            if name not in ALLOWED_ATTRS:
                continue
            if name in ("colspan", "rowspan") and not (value or "").isdigit():
                continue
            clean.append(name if value is None else f'{name}="{escape(value)}"')
        self.out.append(f"<{tag}{' ' + ' '.join(clean) if clean else ''}>")
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS and tag in ALLOWED_TAGS and not self.drop_depth and self.stack \
                and self.stack[-1] == tag:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = RENAME.get(tag, tag)
        if self.drop_stack:
            if tag in self.drop_stack:
                del self.drop_stack[len(self.drop_stack) - 1 - self.drop_stack[::-1].index(tag):]
            return
        if tag not in ALLOWED_TAGS or tag in VOID_TAGS or tag not in self.stack:
            return
        while self.stack:
            open_tag = self.stack.pop()
            self.out.append(f"</{open_tag}>")
            if open_tag == tag:
                break

    def handle_data(self, data):
        if not self.drop_depth:
            self.out.append(escape(data))

    def close(self):
        super().close()
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")


def sanitize_html(html: str) -> str:
    parser = _Sanitizer()
    parser.feed(html or "")
    parser.close()
    return "".join(parser.out)
