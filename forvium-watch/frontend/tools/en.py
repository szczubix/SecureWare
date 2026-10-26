"""Slownik angielski paneli (zrodlo): python3 tools/en.py > shared/i18n-en.js

Kompletnosc sprawdza tools/check_i18n.py (CI): kazdy tr("...") ma tlumaczenie.
"""
import json

EN = {
    # --- wspolne
    "Błąd": "Error", "Błąd ": "Error ", "E-mail": "E-mail", "Hasło": "Password", "Kod MFA": "MFA code",
    "Hasła nie są takie same.": "The passwords do not match.", "Zapisz": "Save", "Anuluj": "Cancel",
    "Wyślij": "Send", "Otwórz": "Open", "Zamknij": "Close", "Usuń": "Delete", "Szukaj": "Search",
    "Szczegóły": "Details", "Nazwa": "Name", "Status": "Status", "Status: ": "Status: ", "Data": "Date",
    "Czas": "Time", "Start": "Start", "Koniec": "End", "Okres": "Period", "Utworzono": "Created",
    "Aktualizacja": "Updated", "Zakres": "Scope", "Zakres: ": "Scope: ", "Operator": "Operator",
    "Operator: ": "Operator: ", "Organizacja": "Organization", "Organizacja: ": "Organization: ",
    "Powód": "Reason", "Powód: ": "Reason: ", "Rola": "Role", "Tryb": "Mode", "Tryb: ": "Mode: ",
    "Numer": "Number", "Temat": "Subject", "Priorytet": "Priority", "Priorytet: ": "Priority: ",
    "Zgłoszenie": "Ticket", "Zgłoszenie: ": "Ticket: ", "Zgłoszenia": "Tickets", "Wiadomość": "Message",
    "Odpowiedź": "Reply", "Notatka": "Note", "Notatka (opcjonalnie)": "Note (optional)", "tak": "yes",
    "nie": "no", "brak": "none", "Brak.": "None.", "Ładowanie…": "Loading…", "Konto": "Account",
    "Konto: ": "Account: ", "Powiadomienia": "Notifications", "Brak powiadomień.": "No notifications.",
    "Wyloguj": "Sign out", "Imię i nazwisko": "Full name", "Pobierz PDF": "Download PDF", "Plan": "Plan",
    "Plan: ": "Plan: ", "Jednostki": "Units", "Technologie": "Technologies", "CVE": "CVE",
    "Diagnostyka": "Diagnostics", "Dashboard": "Dashboard", "Członkowie": "Members", "Organizacje": "Organizations",
    "Dostęp serwisowy": "Service access", "Nie udało się pobrać pliku (": "The file could not be downloaded (",
    "Brak wiadomości.": "No messages.", "Brak nagrania tej sesji.": "There is no recording of this session.",
    "Nagranie": "Recording", "Zakończ": "End", "Odrzuć": "Reject", "Potwierdź": "Confirm", "Zatwierdź": "Approve",
    "Cofnij": "Revoke", "Klucz bezpieczeństwa": "Security key", "Forvium Watch": "Forvium Watch",
    "Forvium Admin": "Forvium Admin", "Support Forvium": "Forvium support", "Support L1": "Support L1",
    "Support L2": "Support L2", "Kierownik supportu": "Support lead", "Waga": "Severity", "Alert": "Alert",

    # --- etykiety stanow
    "aktywne": "active", "czeka na aktywację": "awaiting activation", "zablokowane": "blocked",
    "zablokowane przez Forvium": "blocked by Forvium", "nieaktywne": "inactive", "otwarte": "open",
    "w toku": "in progress", "zamknięte": "closed", "niski": "low", "normalny": "normal", "wysoki": "high",
    "krytyczny": "critical", "właściciel": "owner", "administrator": "administrator", "członek": "member",
    "podgląd": "viewer", "czeka na decyzję": "awaiting decision", "czeka na drugą osobę": "awaiting second person",
    "zatwierdzona": "approved", "odrzucona": "rejected", "anulowana": "cancelled", "wygasła": "expired",
    "procedura awaryjna": "emergency procedure", "aktywna": "active", "cofnięta": "revoked",
    "cofnięta ": "revoked ", "każda": "any", "zgoda cofnięta": "consent revoked", "standardowy": "standard",
    "zatrzymane": "stopped", "działa": "running", "klient": "customer",
    "audytor (cała platforma)": "auditor (whole platform)", "włączone": "enabled", "wyłączone": "disabled",
    "decyzja klienta": "customer decision", "decyzja klienta (2 osoby)": "customer decision (2 people)",
    "zgoda stała": "standing consent",
    "Dashboard organizacji": "Organization dashboard", "Struktura jednostek": "Unit structure",
    "Technologie i CVE": "Technologies and CVEs", "Błędy i stan konfiguracji": "Errors and configuration status",
    "Incydent bezpieczeństwa": "Security incident", "Krytyczna awaria": "Critical outage",
    "Integralność danych": "Data integrity",
    # widoki w nagraniu / podgladzie (nazwy z backendu: support_access/summary.py)
    "Lista CVE": "CVE list", "Stan konfiguracji": "Configuration status", "Błędy": "Errors",

    # --- aktywacja konta
    "Forvium Admin – aktywacja konta operatora": "Forvium Admin – operator account activation",
    "Forvium Watch – aktywacja konta": "Forvium Watch – account activation",
    "Sprawdzanie linku aktywacyjnego…": "Checking the activation link…",
    "Brak tokenu aktywacyjnego w linku.": "The link has no activation token.",
    "Konto aktywne": "Account active",
    "Możesz się zalogować hasłem i kodem z aplikacji uwierzytelniającej.":
        "You can now sign in with your password and authenticator app code.",
    "Przejdź do logowania": "Go to sign-in", "Aktywacja konta": "Account activation",
    "Hasło (min. {n} znaków)": "Password (min. {n} characters)",
    "Najlepsza jest długa fraza z kilku słów. Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego "
    "adresu e-mail lub imienia.":
        "A long phrase of several words works best. The password must not come from known data breaches or "
        "contain your e-mail address or name.",
    "Powtórz hasło": "Repeat password", "Aplikacja uwierzytelniająca (MFA)": "Authenticator app (MFA)",
    "Dodaj konto w aplikacji (np. Google Authenticator, Microsoft Authenticator, Aegis): otwórz link na telefonie "
    "albo wpisz klucz ręcznie.":
        "Add the account in your app (e.g. Google Authenticator, Microsoft Authenticator, Aegis): open the link on "
        "your phone or enter the key manually.",
    "Dodaj do aplikacji uwierzytelniającej": "Add to authenticator app", "Klucz: ": "Key: ",
    "Kod z aplikacji": "App code", "Link jest jednorazowy i ważny do {until}.": "The link is single-use and valid until {until}.",
    "Aktywuj konto": "Activate account",

    # --- haslo
    "Zmiana hasła": "Change password", "Zmiana hasła.": "Password change.", "Wymagana zmiana hasła": "Password change required",
    "Obecne hasło": "Current password", "Nowe hasło (min. 12 znaków)": "New password (min. 12 characters)",
    "Powtórz nowe hasło": "Repeat new password", "Zmień hasło": "Change password",
    "Hasło zmienione. Pozostałe sesje zostały wylogowane.": "Password changed. Your other sessions have been signed out.",
    "Twoje hasło nie spełnia polityki bezpieczeństwa (np. wystąpiło w znanym wycieku danych). Ustaw nowe, aby "
    "kontynuować.":
        "Your password does not meet the security policy (e.g. it appeared in a known data breach). Set a new one "
        "to continue.",
    "Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego adresu e-mail lub imienia.":
        "The password must not come from known data breaches or contain your e-mail address or name.",
    "Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego adresu e-mail lub imienia. Najlepsze są "
    "długie frazy, np. kilka słów.":
        "The password must not come from known data breaches or contain your e-mail address or name. Long phrases, "
        "e.g. several words, work best.",

    # --- panel klienta: logowanie, tryb wsparcia
    "Logowanie": "Sign in", "Zaloguj": "Sign in",
    "Potwierdź kodem MFA z aplikacji uwierzytelniającej:": "Confirm with the MFA code from your authenticator app:",
    "Widok operatora Forvium": "Forvium operator view",
    "Sesja wsparcia Forvium zakończona": "Forvium support session ended",
    "Dostęp serwisowy wygasł lub został zakończony. Możesz zamknąć tę kartę.":
        "Service access has expired or been ended. You can close this tab.",
    "Pozostały czas: {time}": "Time left: {time}", "Klient widzi ten ekran na żywo": "The customer sees this screen live",
    "Zakończ dostęp": "End access", "Widok użytkownika: ": "User view: ",
    "Ta sekcja nie jest objęta zgodą na dostęp serwisowy.": "This section is not covered by the service access consent.",
    "Forvium Watch – sesja wsparcia": "Forvium Watch – support session",
    "Uruchamianie sesji wsparcia…": "Starting the support session…", "Brak kodu uruchomienia.": "No launch code.",
    "Nie udało się uruchomić sesji wsparcia: ": "The support session could not be started: ",

    # --- panel klienta: zgloszenia
    "Opis problemu": "Problem description",
    "Jeśli support będzie potrzebował wglądu w Twoje dane, poprosi o zgodę na dostęp tylko do odczytu, przypiętą do "
    "tego zgłoszenia.":
        "If support needs to look at your data, they will ask for consent to read-only access, linked to this ticket.",
    "Wyślij zgłoszenie": "Submit ticket", "Zgłoszenia do supportu Forvium": "Tickets to Forvium support",
    "Zgłosił(a)": "Reported by", "Nowe zgłoszenie": "New ticket",
    "Zamknąć {ticket}? Trwające sesje wsparcia oparte na tym zgłoszeniu zostaną zakończone.":
        "Close {ticket}? Ongoing support sessions based on this ticket will be ended.",
    "Zamknij zgłoszenie": "Close ticket", "← Zgłoszenia": "← Tickets", " · status: ": " · status: ",
    " · zgłosił(a): ": " · reported by: ", "Rozmowa": "Conversation",
    "Dostęp serwisowy w tym zgłoszeniu": "Service access in this ticket",
    "Forvium nie prosiło o dostęp w ramach tego zgłoszenia.": "Forvium has not requested access under this ticket.",

    # --- panel klienta: czlonkowie
    "Wysłano zaproszenie na {email}. Link aktywacyjny jest ważny 72 godziny.":
        "An invitation has been sent to {email}. The activation link is valid for 72 hours.",
    "Dodano {email} do organizacji.": "{email} has been added to the organization.", "Zaproś": "Invite",
    "Zresetować dostęp {email}? Hasło i aplikacja uwierzytelniająca tej osoby przestaną działać, a na jej adres "
    "wyślemy nowy link aktywacyjny.":
        "Reset access for {email}? This person's password and authenticator app will stop working, and we will "
        "send a new activation link to their address.",
    "Reset dostępu ": "Access reset ", "Resetuj dostęp": "Reset access", "Zaproś osobę": "Invite a person",
    "Nowa osoba dostanie e-mail z linkiem, ustawi hasło i aplikację uwierzytelniającą. Konta pracowników Forvium nie "
    "da się dodać.":
        "The new person will get an e-mail with a link and will set their password and authenticator app. Forvium "
        "staff accounts cannot be added.",

    # --- panel klienta: dashboard, diagnostyka
    "Krytyczne": "Critical", "Wysokie": "High", "SMTP skonfigurowany: ": "SMTP configured: ",
    "Webhooki: ": "Webhooks: ", " · Sekrety: ": " · Secrets: ", " · Plan: ": " · Plan: ",

    # --- panel klienta: dostep serwisowy
    " · jednostki: ": " · units: ", "Cofnij zgodę": "Revoke consent", "(przedłużona {n}x)": "(extended {n}x)",
    "Podgląd na żywo": "Live view", "Aktywność sesji ": "Session activity ", "Aktywność": "Activity",
    "Dostęp serwisowy Forvium": "Forvium service access",
    "Operator Forvium może zobaczyć Twoją organizację wyłącznie w trybie tylko do odczytu, w zakresie i czasie, które "
    "zatwierdzisz. Trwającą sesję możesz oglądać na żywo i przerwać w każdej chwili.":
        "A Forvium operator can see your organization only in read-only mode, within the scope and time you "
        "approve. You can watch an ongoing session live and stop it at any time.",
    "Brak oczekujących próśb.": "No pending requests.", "Zgody": "Consents", "Podstawa": "Basis",
    "Ważna do": "Valid until", "Historia sesji": "Session history",
    "Pierwszy raport pojawi się po zakończeniu miesiąca.": "The first report will appear after the end of the month.",
    "Raporty dostępu": "Access reports",
    "Co miesiąc: wszystkie prośby Forvium o dostęp, decyzje, sesje wsparcia (czas, zakres, oglądane widoki, "
    "zablokowane próby) i zmiany zgód. Skrót SHA-256 pozwala sprawdzić, że plik nie został zmieniony.":
        "Every month: all Forvium access requests, decisions, support sessions (time, scope, views opened, blocked "
        "attempts) and consent changes. The SHA-256 hash lets you check that the file has not been modified.",
    "Utwórz raport za wybrany miesiąc": "Create a report for the selected month",
    "Potwierdź dostęp (druga osoba) · ": "Confirm access (second person) · ", "Prośba o dostęp · ": "Access request · ",
    "Pierwsze zatwierdzenie: ": "First approval: ",
    ". Twoja organizacja wymaga drugiej osoby - możesz tylko potwierdzić lub zawęzić zakres.":
        ". Your organization requires a second person - you can only confirm or narrow down the scope.",
    "Operator Forvium: ": "Forvium operator: ", " · Czas sesji: ": " · Session duration: ", "Zakres zgody": "Consent scope",
    "Ogranicz do jednostek (brak zaznaczenia = wszystkie dozwolone)": "Limit to units (none selected = all allowed)",
    "Zgoda ważna (godziny)": "Consent valid for (hours)",
    "Zapisano. Dostęp zacznie obowiązywać po potwierdzeniu przez drugą osobę.":
        "Saved. Access takes effect once confirmed by a second person.",
    "Włączenie zatwierdzania przez dwie osoby.": "Enabling two-person approval.",
    "Wyłączenie zatwierdzania przez dwie osoby.": "Disabling two-person approval.",
    "Zatwierdzanie przez dwie osoby": "Two-person approval",
    "Gdy włączone, każdy dostęp serwisowy (i każda zgoda stała) wymaga zatwierdzenia przez dwie różne osoby z Twojej "
    "organizacji. Wyłączenie też wymaga drugiej osoby.":
        "When enabled, every service access (and every standing consent) must be approved by two different people "
        "from your organization. Disabling it also requires a second person.",
    " · zgłoszono wyłączenie (": " · disabling requested (", ") - czeka na drugą osobę": ") - awaiting second person",
    "Potwierdź wyłączenie": "Confirm disabling", "Wyłącz": "Disable", "Włącz": "Enable", "Łączenie…": "Connecting…",
    "Operator {operator} ogląda teraz: {view} · pozostało {minutes} min":
        "Operator {operator} is now viewing: {view} · {minutes} min left",
    "Sesja zakończona.": "Session ended.", "Podgląd na żywo · sesja ": "Live view · session ",
    "Przerwij sesję": "Stop session", "Ostatnie operacje operatora": "Operator's latest operations",
    "Nagranie sesji · ": "Session recording · ", "Klatka {n}/{total} · {at} · widok: {view}": "Frame {n}/{total} · {at} · view: {view}",
    "Potwierdzenie zgody stałej.": "Confirming the standing consent.", "Zgody stałe": "Standing consents",
    "Zgoda stała pozwala supportowi Forvium otwierać sesje tylko do odczytu bez każdorazowego pytania - w granicach "
    "poniżej. O każdym takim dostępie dostaniesz powiadomienie, a zgodę można cofnąć w każdej chwili (kończy to też "
    "trwające sesje).":
        "A standing consent lets Forvium support open read-only sessions without asking each time - within the "
        "limits below. You will be notified of every such access, and the consent can be revoked at any time "
        "(this also ends ongoing sessions).",
    " Przy zatwierdzaniu przez dwie osoby nowa zgoda stała zacznie działać po potwierdzeniu przez drugą osobę.":
        " With two-person approval, a new standing consent takes effect once confirmed by a second person.",
    "Sesja do": "Session up to", "Role supportu": "Support roles", "Dodaj zgodę stałą": "Add a standing consent",
    "Ogranicz do jednostek (brak zaznaczenia = wszystkie)": "Limit to units (none selected = all)",
    "Tylko dla ról supportu (brak zaznaczenia = każda)": "Only for support roles (none selected = any)",
    "Maksymalny czas sesji (min)": "Maximum session duration (min)", "Ważna przez (dni)": "Valid for (days)",
    "Potwierdź kodem MFA": "Confirm with MFA code", "Udziel zgody stałej": "Grant standing consent",

    # --- panel admin: logowanie, nawigacja
    "Ta operacja wymaga klucza bezpieczeństwa (WebAuthn). Dodaj klucz w zakładce Konto.":
        "This operation requires a security key (WebAuthn). Add a key in the Account tab.",
    "Ponowna weryfikacja MFA - podaj kod z aplikacji uwierzytelniającej:":
        "MFA re-verification - enter the code from your authenticator app:",
    "Zrzut widoku sesji": "Session view snapshot",
    "Podaj kod MFA albo użyj klucza bezpieczeństwa.": "Enter an MFA code or use a security key.",
    "Logowanie operatora": "Operator sign-in", "Zaloguj kodem MFA": "Sign in with MFA code",
    "Zaloguj kluczem bezpieczeństwa": "Sign in with security key", "Użytkownicy": "Users",
    "Moje prośby": "My requests", "Operatorzy": "Operators", "Nadzór sesji": "Session oversight", "Alerty": "Alerts",
    "Audyt": "Audit", "Raporty": "Reports",

    # --- panel admin: uzytkownicy i prosba o dostep
    "Szukaj po e-mailu lub nazwie": "Search by e-mail or name", "Standardowy (zgoda klienta)": "Standard (customer consent)",
    "AWARYJNY – Break Glass (bez zgody klienta)": "EMERGENCY – Break Glass (without customer consent)",
    "Procedura awaryjna: wymaga zatwierdzenia przez oficera bezpieczeństwa, klient i zespół bezpieczeństwa zostaną "
    "powiadomieni, a sesja podlega obowiązkowemu przeglądowi.":
        "Emergency procedure: requires approval by a security officer, the customer and the security team will be "
        "notified, and the session is subject to a mandatory review.",
    "Kategoria incydentu": "Incident category", "{n} / min. {min} znaków": "{n} / min. {min} characters",
    "Wysłanie prośby o dostęp.": "Sending the access request.",
    "Prośba zatwierdzona automatycznie (zgoda stała klienta). Możesz uruchomić sesję w zakładce Moje prośby.":
        "Request approved automatically (customer's standing consent). You can start the session in the My requests tab.",
    "Wniosek awaryjny wysłany do oficerów bezpieczeństwa.": "Emergency request sent to the security officers.",
    "Prośba wysłana. Klient otrzymał powiadomienie w aplikacji i e-mail.":
        "Request sent. The customer has received an in-app notification and an e-mail.",
    "Sesja w trybie READ_ONLY, wymaga zgody klienta. Maksymalny czas: ":
        "READ_ONLY session, requires customer consent. Maximum duration: ",
    "Użytkownik referencyjny": "Reference user", "Powód dostępu / uzasadnienie": "Access reason / justification",
    "Numer zgłoszenia": "Ticket number", "Czas dostępu (min)": "Access duration (min)",
    "Wysłanie potwierdzisz kluczem bezpieczeństwa.": "You will confirm sending with your security key.",
    "Wysłanie potwierdzisz kodem MFA.": "You will confirm sending with an MFA code.",
    "Wyślij prośbę o dostęp": "Send access request", "← Użytkownicy": "← Users", " · ID ": " · ID ",
    "(powód: {reason})": "(reason: {reason})",
    "Konto nie jest aktywne - dostęp serwisowy niedostępny.": "The account is not active - service access unavailable.",
    "Użytkownik nie należy do żadnej organizacji.": "The user does not belong to any organization.",
    "Odblokowanie konta ": "Unblocking account ", "Odblokuj konto": "Unblock account",
    "Powód blokady (zobaczą go administratorzy organizacji klienta):":
        "Reason for blocking (the customer's organization administrators will see it):",
    "Blokada konta ": "Blocking account ", "Zablokuj konto": "Block account",
    "Powód resetu dostępu (np. zgubiony telefon jedynego właściciela). Nowy link trafi na e-mail tej osoby:":
        "Reason for the access reset (e.g. the only owner lost their phone). The new link will go to this person's e-mail:",
    "Nowy link aktywacyjny dla ": "New activation link for ", "Wysłano nowy link na adres ": "A new link has been sent to ",
    "Wyślij ponownie link aktywacyjny": "Resend activation link",
    "Blokada wylogowuje użytkownika i kończy sesje wsparcia, w których jest użytkownikiem referencyjnym. Forvium nie "
    "zmienia haseł ani MFA klientów.":
        "Blocking signs the user out and ends support sessions in which they are the reference user. Forvium does "
        "not change customers' passwords or MFA.",

    # --- panel admin: organizacje
    "Szukaj po nazwie": "Search by name",
    "Utworzono organizację. Link aktywacyjny wysłano na {email} (ważny 72 h).":
        "Organization created. An activation link has been sent to {email} (valid for 72 h).",
    "Utworzono organizację. {email} został właścicielem.": "Organization created. {email} is now the owner.",
    "E-mail właściciela": "Owner's e-mail", "Imię i nazwisko właściciela": "Owner's full name",
    "Właściciel sam ustawi hasło i MFA (link w e-mailu). Forvium nie poznaje jego hasła.":
        "The owner sets their own password and MFA (link in the e-mail). Forvium never learns their password.",
    "Utwórz organizację": "Create organization", "Nowa organizacja": "New organization",
    "Otwarte zgłoszenia": "Open tickets",
    "Administratorzy organizacji dostaną powiadomienie o zmianie.": "The organization's administrators will be notified of the change.",
    "Dane organizacji": "Organization details", "← Organizacje": "← Organizations", " · utworzona ": " · created ",
    " · zatwierdzanie przez dwie osoby: ": " · two-person approval: ",
    "Członkami zarządza klient (zaproszenia w app). Forvium może zablokować konto.":
        "Members are managed by the customer (invitations in the app). Forvium can block an account.",
    "Język": "Language", "Język organizacji (powiadomienia, e-maile, raporty)": "Organization language (notifications, e-mails, reports)",
    "polski": "Polish", "angielski": "English", " · język: ": " · language: ", "2 osoby": "2 people",
    "Utworzenie organizacji {name}": "Creating the organization {name}",
    "Zmiana danych organizacji {name}": "Changing the details of the organization {name}",
    "Odblokowanie {email}": "Unblocking {email}", "Blokada {email}": "Blocking {email}",
    "Zatwierdzenie roli {role} dla {email}": "Approving role {role} for {email}",
    "Odrzucenie roli dla {email}": "Rejecting the role for {email}", "Nowy operator {email}": "New operator {email}",

    # --- panel admin: zgloszenia
    "Wszystkie": "All", "Otwarte": "Open", "W toku": "In progress", "Zamknięte": "Closed",
    "Zamknąć {ticket}? Aktywne sesje wsparcia na tym zgłoszeniu zostaną zakończone.":
        "Close {ticket}? Active support sessions on this ticket will be ended.",
    "Zakończono sesje wsparcia: {n}.": "Support sessions ended: {n}.", "Otwórz ponownie": "Reopen",
    "Utworzono zgłoszenie {ticket}.": "Ticket {ticket} created.",
    "Dostęp serwisowy zawsze wymaga otwartego zgłoszenia danej organizacji. Zamknięcie zgłoszenia kończy powiązane "
    "sesje.":
        "Service access always requires an open ticket of the organization. Closing the ticket ends the related sessions.",
    "Utwórz zgłoszenie": "Create ticket", " notatka wewnętrzna (klient jej nie zobaczy)": " internal note (the customer will not see it)",
    " · priorytet: ": " · priority: ", "Rozmowa z klientem": "Conversation with the customer",
    " · NOTATKA WEWNĘTRZNA": " · INTERNAL NOTE", "Prośby o dostęp w tym zgłoszeniu": "Access requests in this ticket",

    # --- panel admin: operatorzy
    " (wymaga zatwierdzenia)": " (requires approval)", "Zmiana roli {email}": "Role change for {email}",
    "Rola uprzywilejowana czeka na zatwierdzenie przez oficera bezpieczeństwa.":
        "The privileged role is awaiting approval by a security officer.",
    "Zmień rolę": "Change role", "Odblokuj": "Unblock", "Powód blokady operatora:": "Reason for blocking the operator:",
    "Zablokuj": "Block", "Nowy link aktywacyjny dla {email}": "New activation link for {email}",
    "Wysłano nowy link.": "A new link has been sent.", "Wyślij link ponownie": "Resend link",
    "Zatwierdź rolę": "Approve role", "Powód odrzucenia (opcjonalnie):": "Reason for rejection (optional):",
    " (Ty)": " (you)", " (czeka)": " (pending)", "Link aktywacyjny wysłano na {email}.": "An activation link has been sent to {email}.",
    "Operator sam ustawi hasło i MFA. Role uprzywilejowane nadaje się później - wymagają zatwierdzenia przez oficera "
    "bezpieczeństwa.":
        "The operator sets their own password and MFA. Privileged roles are granted later - they require approval "
        "by a security officer.",
    "Dodaj operatora": "Add operator", "Nowy operator": "New operator", "Operatorzy Forvium": "Forvium operators",
    "Każda zmiana wymaga ponownej weryfikacji i trafia do audytu. Nie możesz zmienić własnej roli ani zablokować "
    "własnego konta.":
        "Every change requires re-verification and is recorded in the audit log. You cannot change your own role "
        "or block your own account.",
    "Zmiana roli": "Role change", "Klucz": "Key",

    # --- panel admin: moje prosby, nadzor
    "O ile minut przedłużyć sesję? (maks. 15)": "Extend the session by how many minutes? (max. 15)",
    "Powód przedłużenia (klient zobaczy go w powiadomieniu):": "Reason for the extension (the customer will see it in the notification):",
    "Przedłużenie sesji.": "Session extension.", "Przedłuż": "Extend", "Zakończ sesję": "End session",
    "Uruchomienie sesji wsparcia.": "Starting the support session.",
    "Otwórz sesję wsparcia (kod ważny 60 s)": "Open the support session (code valid for 60 s)",
    "Uruchom sesję": "Start session", "Moje prośby o dostęp": "My access requests", "Zgoda do": "Consent until",
    "Aktywne": "Active", "Zakończone": "Ended", "Wygasłe": "Expired", "Cofnięte": "Revoked",
    "Zakończyć tę sesję wsparcia?": "End this support session?", "Nadzór sesji wsparcia": "Support session oversight",

    # --- panel admin: audyt
    "ID operatora": "Operator ID", "ID organizacji": "Organization ID", "ID sesji": "Session ID",
    "Akcja (prefiks)": "Action (prefix)", "Od (RRRR-MM-DD)": "From (YYYY-MM-DD)", "Do (RRRR-MM-DD)": "To (YYYY-MM-DD)",
    "Każdy wynik": "Any outcome", "Sukces": "Success", "Odmowa": "Denied", "Tylko Break Glass": "Break Glass only",
    "Wynik": "Outcome", "Eksport CSV": "Export CSV", "Wyniki {from}–{to} z {total}": "Results {from}–{to} of {total}",
    "Akcja": "Action", "Wykonawca": "Actor", "W imieniu": "On behalf of", "Operacja API": "API operation",
    "← Poprzednie": "← Previous", "Następne →": "Next →",

    # --- panel admin: Break Glass
    "Wniosek Break Glass · ": "Break Glass request · ", " · Organizacja: ": " · Organization: ",
    "Kategoria: ": "Category: ", " · Czas: ": " · Duration: ", " min · Wygasa: ": " min · Expires: ",
    "Zatwierdzenie Break Glass.": "Approving Break Glass.", "Zatwierdź (4 oczy)": "Approve (four eyes)",
    "Powód odrzucenia:": "Reason for rejection:", "Ustalenia przeglądu (min. 50 znaków)": "Review findings (min. 50 characters)",
    "Przegląd po incydencie · ": "Post-incident review · ", "Wnioskował: ": "Requested by: ",
    " · Zatwierdził: ": " · Approved by: ", "Sesje: ": "Sessions: ",
    "Zdarzenia Break Glass w audycie": "Break Glass events in the audit log",
    "Zakończ przegląd i wyślij raport klientowi": "Complete the review and send the report to the customer",
    "Wnioski awaryjne wymagają zatwierdzenia przez innego oficera bezpieczeństwa niż wnioskujący, a każde użycie - "
    "niezależnego przeglądu.":
        "Emergency requests must be approved by a security officer other than the requester, and every use requires "
        "an independent review.",
    "Oczekujące na zatwierdzenie": "Awaiting approval", "Brak wniosków.": "No requests.", "Do przeglądu": "To review",

    # --- panel admin: nagrania, alerty, zadania, raporty
    "Nagranie sesji ": "Session recording ",
    "Nagranie zawiera dane klienta. Otwarcie każdej klatki jest rejestrowane w audycie.":
        "The recording contains customer data. Opening each frame is recorded in the audit log.",
    "Przyjęte": "Acknowledged", "Rozwiązane": "Resolved", "Jak rozwiązano alert?": "How was the alert resolved?",
    "Przyjmij": "Acknowledge", "Rozwiąż": "Resolve", "Zadania w tle": "Background jobs",
    "Zadania nie działają: ": "Jobs not running: ", ". Sprawdź kontener worker.": ". Check the worker container.",
    "Zadanie": "Job", "Ostatni udany przebieg": "Last successful run", "Przebiegi / błędy": "Runs / failures",
    "Ostatni błąd": "Last error", "Stan": "State", "Alerty bezpieczeństwa": "Security alerts",
    "Raporty dostępu serwisowego": "Service access reports",
    "Raporty miesięczne tworzą się automatycznie po zakończeniu miesiąca: dla każdej organizacji (wysyłany klientowi) "
    "i zbiorczy dla audytorów. Każde pobranie trafia do audytu.":
        "Monthly reports are created automatically after the end of the month: one per organization (sent to the "
        "customer) and a combined one for auditors. Every download is recorded in the audit log.",
    "Utwórz raport audytora za miesiąc": "Create an auditor report for a month", "Rodzaj": "Type",

    # --- panel admin: klucze bezpieczenstwa
    "Usunąć klucz \"{name}\"?": "Delete the key \"{name}\"?", "Usunięcie klucza.": "Deleting the key.",
    "Klucze bezpieczeństwa (WebAuthn / passkeys)": "Security keys (WebAuthn / passkeys)",
    "Klucz sprzętowy FIDO2 lub passkey z weryfikacją (PIN / biometria). Zastępuje kod TOTP przy ponownej weryfikacji i "
    "jest wymagany w procedurze Break Glass.":
        "A FIDO2 hardware key or a passkey with verification (PIN / biometrics). It replaces the TOTP code for "
        "re-verification and is required for the Break Glass procedure.",
    "Dodany": "Added", "Ostatnio użyty": "Last used", "Nazwa nowego klucza": "New key name",
    "Dodanie klucza bezpieczeństwa.": "Adding a security key.", "Dodaj klucz": "Add key",
}

if __name__ == "__main__":
    print("// Wygenerowane: python3 tools/en.py > shared/i18n-en.js - nie edytuj recznie.")
    print("window.FW_DICT_EN = " + json.dumps(dict(sorted(EN.items())), ensure_ascii=False, indent=1) + ";")
