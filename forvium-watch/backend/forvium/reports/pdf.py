"""Renderowanie raportu dostepu do PDF (fpdf2, czcionka DejaVu z polskimi znakami)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

from forvium.core.i18n import L, tr, tr_stored
from forvium.reports.service import KIND_CUSTOMER, ReportData, period_label
from forvium.support_access.summary import END_REASON_LABELS

FONTS = Path(__file__).parent / "fonts"
STATUS_LABELS = {
    "pending": "czeka na decyzję", "pending_second_approval": "czeka na 2. zatwierdzenie",
    "pending_customer_confirmation": "czeka na 2. osobę", "approved": "zatwierdzona",
    "rejected": "odrzucona", "cancelled": "anulowana", "expired": "wygasła bez decyzji",
}
STANDING_LABELS = {"created": "utworzona", "confirmed": "potwierdzona", "revoked": "cofnięta"}


class _Pdf(FPDF):
    title_text = ""
    lang = "pl"

    def header(self):
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, self.title_text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, "Forvium Watch · " + L("strona {page}", page=self.page_no()).render(self.lang) + "/{nb}",
                  align="C")


def _section(pdf: _Pdf, title: str) -> None:
    if pdf.get_y() > pdf.h - 45:  # naglowek sekcji nie zostaje sam na dole strony
        pdf.add_page()
    pdf.ln(3)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 8.5)


def _table(pdf: _Pdf, headings: list[str], rows: list[list[str]], widths: list[int], empty: str) -> None:
    if not rows:
        pdf.set_font("DejaVu", "", 9.5)
        pdf.multi_cell(0, 6, empty, new_x="LMARGIN", new_y="NEXT")
        return
    pdf.set_font("DejaVu", "", 8)
    with pdf.table(col_widths=widths, headings_style=FontFace(emphasis="BOLD", fill_color=(231, 236, 243)),
                   line_height=4.6, text_align="LEFT") as table:
        table.row(headings)
        for r in rows:
            table.row([str(c) for c in r])


def render(data: ReportData) -> bytes:
    lang = data.lang

    def t(text: str, **params) -> str:
        return L(text, **params).render(lang)

    customer = data.kind == KIND_CUSTOMER
    pdf = _Pdf(orientation="L", format="A4")
    pdf.lang = lang
    pdf.add_font("DejaVu", "", str(FONTS / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(FONTS / "DejaVuSans-Bold.ttf"))
    label = period_label(data.period_start, lang)
    pdf.title_text = (t("Raport dostępu serwisowego Forvium · {org} · {period}", org=data.organization_name,
                        period=label) if customer
                      else t("Raport audytora: dostęp serwisowy Forvium (cała platforma) · {period}", period=label))
    pdf.set_title(pdf.title_text)
    pdf.set_author("Forvium Watch")
    pdf.set_creation_date(datetime.now(UTC))
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, t("Raport dostępu serwisowego") if customer else t("Raport audytora - dostęp serwisowy"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    who = t("Organizacja: {org}", org=data.organization_name) if customer else t("Zakres: wszystkie organizacje")
    last_day = data.period_end - timedelta(days=1)
    pdf.multi_cell(0, 5.5, "\n".join([
        who, t("Okres: {start} - {end} (czas UTC)", start=f"{data.period_start:%Y-%m-%d}", end=f"{last_day:%Y-%m-%d}"),
        t("Wygenerowano: {at} UTC", at=f"{datetime.now(UTC):%Y-%m-%d %H:%M}")]),
                   new_x="LMARGIN", new_y="NEXT")

    _section(pdf, t("Podsumowanie"))
    minutes = sum(s["minutes"] for s in data.sessions)
    bg = sum(1 for r in data.requests if r["break_glass"])
    summary = [
        [t("Prośby o dostęp"), str(len(data.requests))],
        [t("Sesje wsparcia (tylko odczyt)"), t("{n} (łącznie {minutes} min)", n=len(data.sessions),
                                                 minutes=f"{minutes:.1f}")],
        [t("Procedura awaryjna (Break Glass)"), str(bg)],
        [t("Zablokowane próby operacji"), str(data.denied_attempts)],
        [t("Zmiany zgód stałych"), str(len(data.standing))],
        [t("Otwarcia nagrań sesji przez Forvium"), str(len(data.recordings_viewed))],
    ]
    if not customer:
        summary.append([t("Alerty bezpieczeństwa"), str(len(data.alerts))])
    _table(pdf, [t("Pozycja"), t("Wartość")], summary, [90, 80], "")
    if customer and not data.requests and not data.sessions:
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 10)
        pdf.multi_cell(0, 6, t("W tym okresie Forvium nie prosiło o dostęp i nie korzystało z dostępu "
                               "serwisowego do Twojej organizacji."), new_x="LMARGIN", new_y="NEXT")

    org_col = [] if customer else [t("Organizacja")]
    org_w = [] if customer else [35]

    _section(pdf, t("Prośby o dostęp"))
    _table(pdf, [t("Data"), t("Zgłoszenie"), *org_col, t("Operator"), t("Powód"), t("Zakres"), t("Status"),
                 t("Decyzja")],
           [[r["created_at"], r["ticket"] + (" (Break Glass)" if r["break_glass"] else ""),
             *([r["organization"]] if not customer else []), r["operator"], r["reason"], r["scopes"],
             tr(STATUS_LABELS.get(r["status"], r["status"]), lang), r["decided_by"]] for r in data.requests],
           [26, 26, *org_w, 38, 70 - (0 if customer else 20), 45 - (0 if customer else 10), 28, 34 - (0 if customer else 5)],
           t("Brak próśb o dostęp w tym okresie."))

    def end_reason(code: str | None) -> str:
        return tr(END_REASON_LABELS.get(code, code), lang) if code else t("trwa")

    _section(pdf, t("Sesje wsparcia"))
    _table(pdf, [t("Start"), t("Zgłoszenie"), *org_col, t("Operator"), t("Min"), t("Przedł."), t("Oglądane widoki"),
                 t("Operacje / zablok."), t("Zakończenie")],
           [[s["started_at"], s["ticket"], *([s["organization"]] if not customer else []), s["operator"],
             s["minutes"], s["extensions"], ", ".join(tr(v, lang) for v in s["views"]) or "—",
             f"{s['api_calls']} / {s['denied']}", end_reason(s["end_reason"])]
            for s in data.sessions],
           [26, 24, *org_w, 38, 12, 14, 64 - (0 if customer else 20), 24, 65 - (0 if customer else 15)],
           t("Brak sesji wsparcia w tym okresie."))

    _section(pdf, t("Zgody stałe i nagrania"))
    rows = [[e["at"], t("zgoda stała {action}", action=STANDING_LABELS.get(e["action"], e["action"])), e["by"],
             e["organization"] or "—"] for e in data.standing]
    rows += [[e["at"], t("otwarcie nagrania sesji przez Forvium"), e["by"], e["organization"] or "—"]
             for e in data.recordings_viewed]
    _table(pdf, [t("Czas"), t("Zdarzenie"), t("Kto"), t("Organizacja")], sorted(rows), [32, 90, 70, 75],
           t("Brak zmian zgód stałych i otwarć nagrań."))

    if not customer:
        _section(pdf, t("Break Glass - przeglądy"))
        _table(pdf, [t("Data"), t("Zgłoszenie"), t("Organizacja"), t("Operator"), t("Status"), t("Przegląd")],
               [[r["created_at"], r["ticket"], r["organization"], r["operator"],
                 tr(STATUS_LABELS.get(r["status"], r["status"]), lang), t("zakończony") if r["reviewed"] else t("OCZEKUJE")]
                for r in data.requests if r["break_glass"]],
               [30, 30, 55, 60, 45, 45], t("Procedura awaryjna nie była używana."))
        _section(pdf, t("Alerty bezpieczeństwa"))
        _table(pdf, [t("Czas"), t("Waga"), t("Alert"), t("Status")],
               [[a["at"], a["severity"], tr_stored(a["title"], lang), a["status"]] for a in data.alerts],
               [32, 25, 170, 40], t("Brak alertów w tym okresie."))

    _section(pdf, t("Integralność"))
    pdf.set_font("DejaVu", "", 9)
    pdf.multi_cell(0, 5, t("Zdarzenia audytu w okresie: {n}\nOdcisk zdarzeń audytu (SHA-256): {digest}\n"
                           "Odcisk można porównać z eksportem Audit Log (łańcuch skrótów). Skrót tego pliku PDF jest "
                           "zapisany w Forvium Watch i podany w powiadomieniu o raporcie.",
                           n=data.audit_events, digest=data.audit_digest),
                   new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
