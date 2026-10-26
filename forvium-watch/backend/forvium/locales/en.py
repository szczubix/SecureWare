"""Tlumaczenia angielskie tekstow backendu: tekst zrodlowy (pl) -> en.

Kompletnosc sprawdza tests/test_i18n.py: kazdy polski tekst widoczny dla uzytkownika musi
tu byc, a tlumaczenie musi miec te same parametry {...}.
Nazwy menu w tresciach odpowiadaja angielskiej wersji paneli (frontend/*/i18n-en.js).
"""

EN: dict[str, str] = {
    # ------------------------------------------------------------ dostep i uwierzytelnianie
    "Wymagane uwierzytelnienie.": "Authentication required.",
    "Wymagane uwierzytelnienie operatora.": "Operator authentication required.",
    "Operacja niedostępna w trybie wsparcia Forvium.": "This operation is not available in Forvium support mode.",
    "Operacja niedostępna w trybie wsparcia Forvium lub poza zakresem zgody.":
        "This operation is not available in Forvium support mode or is outside the consented scope.",
    "Nie znaleziono organizacji.": "Organization not found.",
    "Twoje hasło nie spełnia polityki bezpieczeństwa (np. wystąpiło w wycieku) - zmień je.":
        "Your password does not meet the security policy (e.g. it appeared in a data breach) - please change it.",
    "Tryb wsparcia jest tylko do odczytu (READ_ONLY).": "Support mode is read-only (READ_ONLY).",
    "Sesja wsparcia nie obejmuje tej organizacji.": "The support session does not cover this organization.",
    "Brak uprawnień.": "Permission denied.",
    "Brak uprawnień operatora.": "Operator permission denied.",
    "Serwer jest chwilowo przeciążony - spróbuj ponownie.": "The server is temporarily overloaded - please try again.",
    "Nieprawidłowe dane logowania.": "Invalid sign-in details.",
    "To konto loguje się wyłącznie kluczem bezpieczeństwa.": "This account signs in with a security key only.",
    "To konto nie ma klucza bezpieczeństwa - zaloguj się kodem MFA.":
        "This account has no security key - sign in with an MFA code.",
    "Zbyt wiele nieudanych prób. Spróbuj ponownie później.": "Too many failed attempts. Please try again later.",

    # ------------------------------------------------------------ aktywacja i hasla
    "Konto jest już aktywne.": "The account is already active.",
    "panelu operatorów Forvium": "the Forvium operator panel",
    "Link aktywacyjny jest nieprawidłowy, wykorzystany albo wygasł.":
        "The activation link is invalid, already used or expired.",
    "Kod z aplikacji uwierzytelniającej jest nieprawidłowy.": "The authenticator app code is invalid.",
    "Aktywuj konto w {panel}": "Activate your account in {panel}",
    "Dzień dobry {name},\n\nzałożono dla Ciebie konto w {panel}. Aby je aktywować, otwórz link (ważny 72 godziny, "
    "jednorazowy) i ustaw hasło oraz aplikację uwierzytelniającą:\n\n{link}\n\nJeśli nie spodziewasz się tej "
    "wiadomości, zignoruj ją.":
        "Hello {name},\n\nan account has been created for you in {panel}. To activate it, open the link (valid for "
        "72 hours, single use) and set your password and authenticator app:\n\n{link}\n\nIf you were not expecting "
        "this message, please ignore it.",
    "Hasło musi mieć co najmniej {n} znaków.": "The password must be at least {n} characters long.",
    "Hasło może mieć najwyżej {max} znaków.": "The password can be at most {max} characters long.",
    "To hasło występuje w znanych wyciekach danych - wybierz inne.":
        "This password appears in known data breaches - choose a different one.",
    "Hasło nie może zawierać adresu e-mail, imienia, nazwiska ani nazwy Forvium.":
        "The password must not contain your e-mail address, first name, last name or the name Forvium.",
    "Hasło jest zbyt proste (powtórzenia albo sekwencje znaków).":
        "The password is too simple (repeated characters or sequences).",
    "Klucz bezpieczeństwa": "Security key",
    "Nowe hasło musi być inne niż obecne.": "The new password must be different from the current one.",
    "Zmieniono hasło": "Password changed",
    "Hasło do Twojego konta zostało zmienione, a pozostałe sesje wylogowane. Jeśli to nie Ty - natychmiast "
    "skontaktuj się z administratorem.":
        "The password for your account has been changed and your other sessions have been signed out. If this "
        "wasn't you, contact your administrator immediately.",
    "Nieprawidłowe obecne hasło.": "The current password is incorrect.",
    "Nieprawidłowe hasło lub kod MFA.": "Incorrect password or MFA code.",
    "Zmieniono drugi składnik logowania (MFA)": "Second sign-in factor (MFA) changed",
    "Na Twoim koncie ustawiono nowy sekret aplikacji uwierzytelniającej, a pozostałe sesje zostały wylogowane. "
    "Jeśli to nie Ty - natychmiast zmień hasło i skontaktuj się z administratorem organizacji.":
        "A new authenticator app secret has been set on your account and your other sessions have been signed "
        "out. If this wasn't you, change your password immediately and contact your organization administrator.",

    # ------------------------------------------------------------ WebAuthn
    "Wyzwanie WebAuthn jest nieprawidłowe lub wygasło.": "The WebAuthn challenge is invalid or expired.",
    "Nie udało się zweryfikować klucza: {error}": "The security key could not be verified: {error}",
    "Dodano klucz bezpieczeństwa do konta Forvium": "Security key added to your Forvium account",
    "Do Twojego konta dodano klucz '{name}'. Jeśli to nie Ty, natychmiast skontaktuj się z zespołem "
    "bezpieczeństwa.":
        "The key '{name}' has been added to your account. If this wasn't you, contact the security team "
        "immediately.",
    "Nie znaleziono klucza.": "Security key not found.",
    "Usunięto klucz bezpieczeństwa z konta Forvium": "Security key removed from your Forvium account",
    "Z Twojego konta usunięto klucz '{name}'.": "The key '{name}' has been removed from your account.",
    "Najpierw dodaj klucz bezpieczeństwa.": "Add a security key first.",

    # ------------------------------------------------------------ organizacje i czlonkowie
    "Nie znaleziono członka.": "Member not found.",
    "Nieprawidłowy adres e-mail.": "Invalid e-mail address.",
    "Właściciela może dodać tylko właściciel.": "Only an owner can add another owner.",
    "Konta operatora Forvium nie można dodać do organizacji.":
        "A Forvium operator account cannot be added to an organization.",
    "Ta osoba już należy do organizacji.": "This person is already a member of the organization.",
    "Nie możesz zresetować własnego dostępu - poproś innego administratora.":
        "You cannot reset your own access - ask another administrator.",
    "Dostęp właściciela może zresetować tylko inny właściciel.": "Only another owner can reset an owner's access.",
    "Tego konta nie można zresetować.": "This account cannot be reset.",
    "Ta osoba należy też do innych organizacji - reset dostępu wykona support Forvium.":
        "This person also belongs to other organizations - Forvium support will reset their access.",
    "Potwierdź operację kodem z aplikacji uwierzytelniającej.": "Confirm the operation with your authenticator app code.",
    "Zresetowano dostęp {email}": "Access reset for {email}",
    "Zresetował(a): {who}. Nowy link aktywacyjny wysłano na adres tej osoby.":
        "Reset by: {who}. A new activation link has been sent to this person's e-mail address.",
    "Dodano Cię do organizacji {org}": "You have been added to the organization {org}",
    "Rola: {role}. Dodał(a): {who}.": "Role: {role}. Added by: {who}.",

    # ------------------------------------------------------------ panel admin: zarzadzanie
    "Support L1": "Support L1",
    "Support L2": "Support L2",
    "Kierownik supportu": "Support lead",
    "Oficer bezpieczeństwa": "Security officer",
    "Administrator platformy": "Platform administrator",
    "Nieznany plan subskrypcji.": "Unknown subscription plan.",
    "Centrala": "Headquarters",
    "Konto operatora Forvium nie może być właścicielem organizacji klienta.":
        "A Forvium operator account cannot own a customer organization.",
    "Konto wskazanego właściciela jest zablokowane.": "The selected owner's account is blocked.",
    "Nie znaleziono użytkownika.": "User not found.",
    "Konto jest już zablokowane.": "The account is already blocked.",
    "Konto nie jest zablokowane.": "The account is not blocked.",
    "Konto jest zablokowane albo czeka na aktywację.": "The account is blocked or awaiting activation.",
    "Konto nie czeka na aktywację.": "The account is not awaiting activation.",
    "Nie znaleziono operatora.": "Operator not found.",
    "Nieznana rola operatora.": "Unknown operator role.",
    "Rolę uprzywilejowaną nadaje się istniejącemu operatorowi i wymaga ona zatwierdzenia przez oficera "
    "bezpieczeństwa.":
        "A privileged role is granted to an existing operator and requires approval by a security officer.",
    "Konto z tym adresem już istnieje.": "An account with this address already exists.",
    "Nie możesz zmienić własnej roli.": "You cannot change your own role.",
    "Operator ma już tę rolę.": "The operator already has this role.",
    "To ostatni aktywny administrator platformy.": "This is the last active platform administrator.",
    "Brak zmiany roli do zatwierdzenia.": "There is no role change to approve.",
    "Zmianę musi zatwierdzić inna osoba niż zlecający i niż operator, którego dotyczy.":
        "The change must be approved by someone other than the requester and the operator concerned.",
    "Nie możesz zablokować własnego konta.": "You cannot block your own account.",
    "Nie możesz odblokować własnego konta.": "You cannot unblock your own account.",
    "Zgłaszający nie należy do tej organizacji.": "The reporter is not a member of this organization.",
    "Nie znaleziono zgłoszenia.": "Ticket not found.",
    "Nieznany status zgłoszenia.": "Unknown ticket status.",
    "Jesteś właścicielem organizacji {org} w Forvium Watch": "You are the owner of the organization {org} in Forvium Watch",
    "Forvium założyło organizację i wskazało Cię jako właściciela.":
        "Forvium has created the organization and named you as its owner.",
    "Forvium zmieniło dane organizacji {org}": "Forvium changed the details of the organization {org}",
    "Zmiany: {changes}.": "Changes: {changes}.",
    "Forvium zablokowało konto {email}": "Forvium blocked the account {email}",
    "Powód: {reason}": "Reason: {reason}",
    "Twoje konto Forvium Watch zostało zablokowane": "Your Forvium Watch account has been blocked",
    "Powód: {reason}\nW razie pytań skontaktuj się z supportem Forvium.":
        "Reason: {reason}\nIf you have any questions, contact Forvium support.",
    "Forvium odblokowało konto {email}": "Forvium unblocked the account {email}",
    "Konto znów może się logować.": "The account can sign in again.",
    "Forvium zresetowało dostęp {email}": "Forvium reset access for {email}",
    "Powód: {reason}. Link aktywacyjny wysłano na adres tej osoby.":
        "Reason: {reason}. An activation link has been sent to this person's e-mail address.",
    "Do zatwierdzenia: rola {role} dla {email}": "Approval needed: role {role} for {email}",
    "Zlecił: {who}. Zatwierdź albo odrzuć w panelu: Operatorzy.":
        "Requested by: {who}. Approve or reject it in the panel: Operators.",
    "Zmieniono rolę operatora {email}": "Operator role changed for {email}",
    "{old} -> {new} (zmienił: {who}).": "{old} -> {new} (changed by: {who}).",
    "Zatwierdzono rolę {role} dla {email}": "Role {role} approved for {email}",
    "Zlecił: {requester}, zatwierdził: {who}.": "Requested by: {requester}, approved by: {who}.",
    "Odrzucono rolę {role} dla {email}": "Role {role} rejected for {email}",
    "Odrzucił: {who}.": "Rejected by: {who}.",
    "Zablokowano operatora {email}": "Operator {email} blocked",
    "Zablokował: {who}. Powód: {reason}. Zakończone sesje wsparcia: {ended}.":
        "Blocked by: {who}. Reason: {reason}. Support sessions ended: {ended}.",
    "Odblokowano operatora {email}": "Operator {email} unblocked",
    "Odblokował: {who}.": "Unblocked by: {who}.",
    "Forvium otworzyło zgłoszenie {ticket}": "Forvium opened ticket {ticket}",
    "Zgłoszenie {ticket}: {status}": "Ticket {ticket}: {status}",

    # ------------------------------------------------------------ zgloszenia
    "niski": "low",
    "normalny": "normal",
    "wysoki": "high",
    "krytyczny": "critical",
    "otwarte": "open",
    "w toku": "in progress",
    "zamknięte": "closed",
    "Zgłoszenie jest zamknięte - utwórz nowe.": "The ticket is closed - create a new one.",
    "Zgłoszenie jest zamknięte - otwórz je ponownie, aby odpowiedzieć klientowi.":
        "The ticket is closed - reopen it to reply to the customer.",
    "Nowe zgłoszenie {ticket} ({org}, priorytet: {priority})": "New ticket {ticket} ({org}, priority: {priority})",
    "{subject}\nZgłasza: {who}. Szczegóły w panelu: Zgłoszenia.":
        "{subject}\nReported by: {who}. Details in the panel: Tickets.",
    "Odpowiedź klienta w {ticket}": "Customer reply in {ticket}",
    "Klient zamknął zgłoszenie {ticket}": "The customer closed ticket {ticket}",
    "Zamknął: {who}. Zakończone sesje wsparcia: {ended}.": "Closed by: {who}. Support sessions ended: {ended}.",
    "Odpowiedź supportu Forvium w {ticket}": "Forvium support reply in {ticket}",
    "{message}\n\nOdpowiesz w aplikacji: Zgłoszenia.": "{message}\n\nYou can reply in the app: Tickets.",

    # ------------------------------------------------------------ raporty dostepu
    "Nie znaleziono raportu.": "Report not found.",
    "Raport klienta wymaga organizacji, raport audytora - bez niej.":
        "A customer report requires an organization; an auditor report must not have one.",
    "Raport można utworzyć tylko za zakończony okres.": "A report can only be created for a completed period.",
    "Sesje wsparcia: {sessions}, prośby o dostęp: {requests}, zablokowane próby: {denied}.\nSHA-256 pliku: {sha256}":
        "Support sessions: {sessions}, access requests: {requests}, blocked attempts: {denied}.\n"
        "File SHA-256: {sha256}",
    "Raport pobierzesz w aplikacji: Ustawienia -> Dostęp serwisowy -> Raporty dostępu.":
        "Download the report in the app: Settings -> Service access -> Access reports.",
    "Raport pobierzesz w panelu admin: zakładka Raporty.": "Download the report in the admin panel: Reports tab.",
    "Raport dostępu serwisowego Forvium za {period}": "Forvium service access report for {period}",
    "czeka na decyzję": "awaiting decision",
    "czeka na 2. zatwierdzenie": "awaiting 2nd approval",
    "czeka na 2. osobę": "awaiting 2nd person",
    "zatwierdzona": "approved",
    "odrzucona": "rejected",
    "anulowana": "cancelled",
    "wygasła bez decyzji": "expired without decision",
    "utworzona": "created",
    "potwierdzona": "confirmed",
    "cofnięta": "revoked",
    "strona {page}": "page {page}",
    "Raport dostępu serwisowego Forvium · {org} · {period}": "Forvium service access report · {org} · {period}",
    "Raport audytora: dostęp serwisowy Forvium (cała platforma) · {period}":
        "Auditor report: Forvium service access (whole platform) · {period}",
    "Raport dostępu serwisowego": "Service access report",
    "Raport audytora - dostęp serwisowy": "Auditor report - service access",
    "Organizacja: {org}": "Organization: {org}",
    "Zakres: wszystkie organizacje": "Scope: all organizations",
    "Okres: {start} - {end} (czas UTC)": "Period: {start} - {end} (UTC)",
    "Wygenerowano: {at} UTC": "Generated: {at} UTC",
    "Podsumowanie": "Summary",
    "Prośby o dostęp": "Access requests",
    "Sesje wsparcia (tylko odczyt)": "Support sessions (read-only)",
    "{n} (łącznie {minutes} min)": "{n} ({minutes} min in total)",
    "Procedura awaryjna (Break Glass)": "Emergency procedure (Break Glass)",
    "Zablokowane próby operacji": "Blocked operation attempts",
    "Zmiany zgód stałych": "Standing consent changes",
    "Otwarcia nagrań sesji przez Forvium": "Session recordings opened by Forvium",
    "Alerty bezpieczeństwa": "Security alerts",
    "Pozycja": "Item",
    "Wartość": "Value",
    "W tym okresie Forvium nie prosiło o dostęp i nie korzystało z dostępu serwisowego do Twojej organizacji.":
        "In this period Forvium did not request or use service access to your organization.",
    "Organizacja": "Organization",
    "Data": "Date",
    "Zgłoszenie": "Ticket",
    "Operator": "Operator",
    "Powód": "Reason",
    "Zakres": "Scope",
    "Status": "Status",
    "Decyzja": "Decision",
    "Brak próśb o dostęp w tym okresie.": "No access requests in this period.",
    "trwa": "in progress",
    "Sesje wsparcia": "Support sessions",
    "Start": "Start",
    "Min": "Min",
    "Przedł.": "Ext.",
    "Oglądane widoki": "Views opened",
    "Operacje / zablok.": "Operations / blocked",
    "Zakończenie": "End",
    "Brak sesji wsparcia w tym okresie.": "No support sessions in this period.",
    "Zgody stałe i nagrania": "Standing consents and recordings",
    "zgoda stała {action}": "standing consent {action}",
    "otwarcie nagrania sesji przez Forvium": "session recording opened by Forvium",
    "Czas": "Time",
    "Zdarzenie": "Event",
    "Kto": "Who",
    "Brak zmian zgód stałych i otwarć nagrań.": "No standing consent changes or recordings opened.",
    "Break Glass - przeglądy": "Break Glass - reviews",
    "Przegląd": "Review",
    "zakończony": "completed",
    "OCZEKUJE": "PENDING",
    "Procedura awaryjna nie była używana.": "The emergency procedure was not used.",
    "Waga": "Severity",
    "Alert": "Alert",
    "Brak alertów w tym okresie.": "No alerts in this period.",
    "Integralność": "Integrity",
    "Zdarzenia audytu w okresie: {n}\nOdcisk zdarzeń audytu (SHA-256): {digest}\nOdcisk można porównać z eksportem "
    "Audit Log (łańcuch skrótów). Skrót tego pliku PDF jest zapisany w Forvium Watch i podany w powiadomieniu o "
    "raporcie.":
        "Audit events in the period: {n}\nAudit event fingerprint (SHA-256): {digest}\nThe fingerprint can be "
        "compared with the Audit Log export (hash chain). The hash of this PDF file is stored in Forvium Watch and "
        "given in the report notification.",

    # ------------------------------------------------------------ alerty bezpieczenstwa
    "Nie znaleziono alertu.": "Alert not found.",
    "Nieprawidłowy status.": "Invalid status.",
    "Opisz, jak rozwiązano alert.": "Describe how the alert was resolved.",
    "Nie można obsługiwać alertu dotyczącego własnych działań.": "You cannot handle an alert about your own actions.",
    "Seria {n} zablokowanych operacji w sesji wsparcia": "A burst of {n} blocked operations in a support session",
    "Próby użycia tokenu zakończonej sesji wsparcia": "Attempts to use the token of an ended support session",
    "{n} sesji wsparcia operatora w ciągu godziny": "{n} support sessions by one operator within an hour",
    "Sesje operatora w {n} organizacjach w ciągu godziny": "Operator sessions in {n} organizations within an hour",
    "Sesja wsparcia rozpoczęta poza godzinami pracy": "Support session started outside business hours",
    "Blokada konta operatora po nieudanych próbach weryfikacji":
        "Operator account locked after failed verification attempts",
    "Zatwierdzono procedurę Break Glass": "Break Glass procedure approved",
    "[{severity}] {title}": "[{severity}] {title}",
    "Operator: {operator}": "Operator: {operator}",
    "Sesja: {session}": "Session: {session}",
    "Automatyczna akcja: {action}": "Automatic action: {action}",
    "Szczegóły: admin.forvium.com -> Alerty.": "Details: admin.forvium.com -> Alerts.",
    "Alert bezpieczeństwa: {title}": "Security alert: {title}",
    "Alert: {title}": "Alert: {title}",

    # ------------------------------------------------------------ Break Glass
    "Operator {operator} wnioskuje o dostęp awaryjny (Break Glass) do organizacji {org} ({org_id}), zgłoszenie "
    "{ticket}, kategoria {category}, {minutes} min.\nUzasadnienie: {reason}\nWniosek wygasa {deadline} UTC. "
    "Decyzja: admin.forvium.com -> Break Glass.":
        "Operator {operator} requests emergency access (Break Glass) to the organization {org} ({org_id}), ticket "
        "{ticket}, category {category}, {minutes} min.\nJustification: {reason}\nThe request expires at {deadline} "
        "UTC. Decision: admin.forvium.com -> Break Glass.",
    "Wniosek Break Glass ({ticket})": "Break Glass request ({ticket})",
    "Forvium uruchomiło procedurę awaryjną (Break Glass) dla organizacji {org}: operator {operator} może otworzyć "
    "sesję TYLKO DO ODCZYTU do {minutes} min, zgłoszenie {ticket}.\nKategoria incydentu: {category}\nUzasadnienie: "
    "{reason}\nWniosek zatwierdził oficer bezpieczeństwa Forvium ({officer}). Możecie natychmiast cofnąć tę zgodę: "
    "Ustawienia -> Dostęp serwisowy. Po incydencie otrzymacie raport z przeglądu.":
        "Forvium has started the emergency procedure (Break Glass) for the organization {org}: operator {operator} "
        "may open a READ-ONLY session for up to {minutes} min, ticket {ticket}.\nIncident category: {category}\n"
        "Justification: {reason}\nThe request was approved by a Forvium security officer ({officer}). You can "
        "revoke this consent immediately: Settings -> Service access. After the incident you will receive a review "
        "report.",
    "PROCEDURA AWARYJNA Forvium ({ticket})": "Forvium EMERGENCY PROCEDURE ({ticket})",
    "Nie znaleziono wniosku Break Glass.": "Break Glass request not found.",
    "Wniosek musi zatwierdzić inna osoba (zasada 4 oczu).": "The request must be approved by someone else (four-eyes rule).",
    "Wniosek nie oczekuje na zatwierdzenie.": "The request is not awaiting approval.",
    "Break Glass zatwierdzony ({ticket})": "Break Glass approved ({ticket})",
    "Zgoda awaryjna ważna do {until} UTC.": "Emergency consent valid until {until} UTC.",
    "Nie można decydować o własnym wniosku.": "You cannot decide on your own request.",
    "Break Glass odrzucony ({ticket})": "Break Glass rejected ({ticket})",
    "Wniosek odrzucony.": "Request rejected.",
    "Przegląd musi wykonać osoba niezależna od wnioskującego i zatwierdzającego.":
        "The review must be done by someone independent of the requester and the approver.",
    "Wniosek nie wymaga przeglądu.": "The request does not need a review.",
    "Sesja awaryjna wciąż trwa.": "The emergency session is still in progress.",
    "Opisz ustalenia przeglądu (min. 50 znaków).": "Describe the review findings (min. 50 characters).",
    "Przegląd procedury awaryjnej Forvium ({ticket}) został zakończony.":
        "The review of the Forvium emergency procedure ({ticket}) has been completed.",
    "Ustalenia: {notes}": "Findings: {notes}",
    "Sesja {n}:\n{summary}": "Session {n}:\n{summary}",
    "Szczegółowa lista operacji: Ustawienia -> Dostęp serwisowy -> Historia sesji.":
        "Detailed list of operations: Settings -> Service access -> Session history.",
    "Raport z procedury awaryjnej Forvium ({ticket})": "Forvium emergency procedure report ({ticket})",
    "Break Glass - przegląd zakończony ({ticket})": "Break Glass - review completed ({ticket})",

    # ------------------------------------------------------------ ustawienia organizacji
    "Konto operatora Forvium nie może zmieniać ustawień.": "A Forvium operator account cannot change settings.",
    "Wyłączenie musi potwierdzić inna osoba niż zgłaszająca.":
        "Disabling must be confirmed by someone other than the person who requested it.",
    "Potwierdź zmianę kodem MFA.": "Confirm the change with an MFA code.",
    "Włączono zatwierdzanie dostępu serwisowego przez dwie osoby": "Two-person approval of service access enabled",
    "{name} włączył(a) wymóg dwóch zatwierdzeń.": "{name} enabled the two-approval requirement.",
    "Prośba o wyłączenie zatwierdzania przez dwie osoby": "Request to disable two-person approval",
    "{name} chce wyłączyć wymóg dwóch zatwierdzeń dostępu serwisowego Forvium. Zmiana wymaga potwierdzenia przez "
    "inną osobę: Ustawienia -> Dostęp serwisowy.":
        "{name} wants to disable the two-approval requirement for Forvium service access. The change must be "
        "confirmed by another person: Settings -> Service access.",
    "Wyłączono zatwierdzanie dostępu serwisowego przez dwie osoby": "Two-person approval of service access disabled",
    "{name} potwierdził(a) wyłączenie wymogu dwóch zatwierdzeń.":
        "{name} confirmed disabling the two-approval requirement.",

    # ------------------------------------------------------------ nagrania sesji
    "Zrzut widoku jest zbyt duży.": "The view snapshot is too large.",
    "Osiągnięto limit zrzutów w tej sesji.": "The snapshot limit for this session has been reached.",
    "Zbyt częste zrzuty.": "Snapshots are too frequent.",
    "Nie znaleziono sesji.": "Session not found.",
    "Nie znaleziono zrzutu.": "Snapshot not found.",

    # ------------------------------------------------------------ dostep serwisowy
    "TRYB AWARYJNY FORVIUM (BREAK GLASS) — TYLKO ODCZYT": "FORVIUM EMERGENCY MODE (BREAK GLASS) — READ ONLY",
    "TRYB WSPARCIA FORVIUM — TYLKO ODCZYT": "FORVIUM SUPPORT MODE — READ ONLY",
    "Brak aktywnej sesji wsparcia.": "No active support session.",
    "Ta operacja wymaga potwierdzenia kluczem bezpieczeństwa (WebAuthn).":
        "This operation requires confirmation with a security key (WebAuthn).",
    "Wymagana ponowna weryfikacja MFA operatora.": "Operator MFA re-verification required.",
    "Dostęp awaryjny (Break Glass) jest wyłączony.": "Emergency access (Break Glass) is disabled.",
    "Nieznany tryb dostępu.": "Unknown access mode.",
    "Użytkownik referencyjny nie należy do organizacji.": "The reference user is not a member of the organization.",
    "Operator nie może odtwarzać własnego widoku.": "An operator cannot use their own account as the reference user.",
    "Podaj szczegółowe uzasadnienie (min. {n} znaków).": "Give a detailed justification (min. {n} characters).",
    "Wybierz kategorię incydentu.": "Choose an incident category.",
    "Zgłoszenie nie istnieje, jest zamknięte lub dotyczy innej organizacji.":
        "The ticket does not exist, is closed or belongs to another organization.",
    "Nieznany zakres dostępu.": "Unknown access scope.",
    "Wybierz co najmniej jeden zakres.": "Choose at least one scope.",
    "Zakres przekracza uprawnienia operatora.": "The scope exceeds the operator's permissions.",
    "Czas dostępu musi mieścić się w 1-{n} min.": "The access duration must be between 1 and {n} min.",
    "Dostęp serwisowy Forvium zatwierdzony automatycznie ({ticket})":
        "Forvium service access approved automatically ({ticket})",
    "Operator Forvium ({operator}) uzyskał dostęp READ_ONLY do organizacji {org} na podstawie Waszej zgody stałej. "
    "Powód: {reason}. Zgoda ważna do {until} UTC. Możesz ją cofnąć: Ustawienia -> Dostęp serwisowy.":
        "A Forvium operator ({operator}) has been granted READ_ONLY access to the organization {org} based on your "
        "standing consent. Reason: {reason}. The consent is valid until {until} UTC. You can revoke it: Settings -> "
        "Service access.",
    "Forvium prosi o dostęp serwisowy ({ticket})": "Forvium requests service access ({ticket})",
    "Operator Forvium ({operator}) prosi o dostęp serwisowy READ_ONLY do organizacji {org} na {minutes} min. Powód: "
    "{reason}. Zatwierdź lub odrzuć prośbę w aplikacji: Ustawienia -> Dostęp serwisowy.":
        "A Forvium operator ({operator}) requests READ_ONLY service access to the organization {org} for {minutes} "
        "min. Reason: {reason}. Approve or reject the request in the app: Settings -> Service access.",
    "Zatwierdzono automatycznie (zgoda stała {id})": "Approved automatically (standing consent {id})",
    "Nie znaleziono prośby.": "Request not found.",
    "Nie można zatwierdzić własnej prośby o dostęp.": "You cannot approve your own access request.",
    "Konto operatora Forvium nie może zatwierdzać dostępu serwisowego.":
        "A Forvium operator account cannot approve service access.",
    "Prośba nie oczekuje na decyzje.": "The request is not awaiting a decision.",
    "Zgodę musi potwierdzić inna osoba niż pierwsza zatwierdzająca.":
        "The consent must be confirmed by someone other than the first approver.",
    "Zgoda może obejmować tylko zakresy, o które wnioskowano.": "The consent can only cover the requested scopes.",
    "Potwierdzenie może tylko zawęzić jednostki.": "The confirmation can only narrow down the units.",
    "Nieprawidłowe jednostki.": "Invalid units.",
    "Ważność zgody: 1-{n} h.": "Consent validity: 1-{n} h.",
    "Potwierdź dostęp serwisowy Forvium ({ticket})": "Confirm Forvium service access ({ticket})",
    "{name} zatwierdził(a) dostęp serwisowy (zakres: {scopes}). Wasza organizacja wymaga drugiego potwierdzenia: "
    "Ustawienia -> Dostęp serwisowy.":
        "{name} approved service access (scope: {scopes}). Your organization requires a second confirmation: "
        "Settings -> Service access.",
    "Zgoda na dostęp serwisowy ({ticket}) udzielona": "Service access consent granted ({ticket})",
    "Zgoda ważna do {until} UTC, zakres: {scopes}.": "Consent valid until {until} UTC, scope: {scopes}.",
    "Nie można decydować o własnej prośbie.": "You cannot decide on your own request.",
    "Prośba o dostęp serwisowy ({ticket}) odrzucona": "Service access request rejected ({ticket})",
    "Klient odrzucił prośbę o dostęp serwisowy.": "The customer rejected the service access request.",
    "Zakończono sesję wsparcia Forvium ({ticket})": "Forvium support session ended ({ticket})",
    "Operator Forvium {operator} zakończył sesję wsparcia w trybie tylko do odczytu.":
        "Forvium operator {operator} has ended the read-only support session.",
    "Pełna lista operacji: Ustawienia -> Dostęp serwisowy -> Historia sesji.":
        "Full list of operations: Settings -> Service access -> Session history.",
    "Nie znaleziono zgody.": "Consent not found.",
    "Klient cofnął zgodę na dostęp serwisowy": "The customer revoked the service access consent",
    "Wszystkie aktywne sesje wsparcia zostały zakończone.": "All active support sessions have been ended.",
    "Sesje może uruchomić tylko operator, który złożył prośbę.":
        "Only the operator who submitted the request can start the session.",
    "Brak zgody klienta na dostęp serwisowy.": "There is no customer consent for service access.",
    "Zgoda klienta została cofnięta lub wygasła.": "The customer consent has been revoked or has expired.",
    "Zgłoszenie supportowe jest zamknięte.": "The support ticket is closed.",
    "Sesja w ramach tej zgody jest już aktywna.": "A session under this consent is already active.",
    "Zakres zgody nie daje żadnych uprawnień.": "The consent scope does not grant any permissions.",
    "Nieprawidłowy czas sesji.": "Invalid session duration.",
    "PROCEDURA AWARYJNA: rozpoczęto sesję Forvium Break Glass ({ticket})":
        "EMERGENCY PROCEDURE: Forvium Break Glass session started ({ticket})",
    "Rozpoczęto sesję wsparcia Forvium ({ticket})": "Forvium support session started ({ticket})",
    "Operator Forvium {operator} rozpoczął sesję wsparcia w trybie tylko do odczytu (zgłoszenie {ticket}). Sesja "
    "wygasa {until} UTC. Możesz ją zakończyć lub cofnąć zgodę w każdej chwili: Ustawienia -> Dostęp serwisowy.":
        "Forvium operator {operator} has started a read-only support session (ticket {ticket}). The session expires "
        "at {until} UTC. You can end it or revoke the consent at any time: Settings -> Service access.",
    "Break Glass: start sesji ({ticket})": "Break Glass: session started ({ticket})",
    "Operator {operator} rozpoczął sesję awaryjną {session} w organizacji {org} do {until} UTC.":
        "Operator {operator} started emergency session {session} in organization {org} until {until} UTC.",
    "Kod uruchomienia jest nieprawidłowy lub wygasł.": "The launch code is invalid or expired.",
    "Sesja wsparcia jest nieprawidłowa lub zakończona.": "The support session is invalid or has ended.",
    "Sesja wsparcia nie jest już aktywna.": "The support session is no longer active.",
    "Sesja nie jest już aktywna.": "The session is no longer active.",
    "Wykorzystano limit przedłużeń tej sesji.": "The extension limit for this session has been used up.",
    "Przedłużenie: 1-{n} min.": "Extension: 1-{n} min.",
    "Podaj powód przedłużenia.": "Give a reason for the extension.",
    "Nie można przedłużyć: osiągnięto limit czasu sesji lub ważności zgody.":
        "Cannot extend: the session time limit or the consent validity has been reached.",
    "Przedłużono sesję wsparcia Forvium ({ticket})": "Forvium support session extended ({ticket})",
    "Operator {operator} przedłużył sesję tylko do odczytu o {minutes} min (do {until} UTC). Powód: {reason}. Możesz "
    "ją zakończyć w każdej chwili: Ustawienia -> Dostęp serwisowy.":
        "Operator {operator} extended the read-only session by {minutes} min (until {until} UTC). Reason: {reason}. "
        "You can end it at any time: Settings -> Service access.",
    "Break Glass: przedłużenie sesji ({ticket})": "Break Glass: session extended ({ticket})",
    "Sesja {session} przedłużona do {until} UTC. Powód: {reason}":
        "Session {session} extended until {until} UTC. Reason: {reason}",

    # ------------------------------------------------------------ zgody stale
    "Konto operatora Forvium nie może udzielać zgód.": "A Forvium operator account cannot grant consents.",
    "Czas sesji: 1-{n} min.": "Session duration: 1-{n} min.",
    "Ważność zgody stałej: 1-{n} dni.": "Standing consent validity: 1-{n} days.",
    "Nieznana rola supportu.": "Unknown support role.",
    "Potwierdź zgodę stałą kodem MFA.": "Confirm the standing consent with an MFA code.",
    "Potwierdź zgodę stałą na dostęp serwisowy Forvium": "Confirm the standing consent for Forvium service access",
    "Utworzono zgodę stałą na dostęp serwisowy Forvium": "Standing consent for Forvium service access created",
    "{name} udzielił(a) zgody stałej (zakres: {scopes}, do {minutes} min na sesję, ważna do {until}).":
        "{name} granted a standing consent (scope: {scopes}, up to {minutes} min per session, valid until {until}).",
    "Zgoda zacznie obowiązywać po potwierdzeniu przez drugą osobę.":
        "The consent takes effect once confirmed by a second person.",
    "Można ją cofnąć w Ustawienia -> Dostęp serwisowy.": "It can be revoked in Settings -> Service access.",
    "Nie znaleziono zgody stałej.": "Standing consent not found.",
    "Zgoda stała nie czeka na potwierdzenie.": "The standing consent is not awaiting confirmation.",
    "Zgodę stałą musi potwierdzić inna osoba niż tworząca.":
        "The standing consent must be confirmed by someone other than its creator.",

    # ------------------------------------------------------------ podsumowanie sesji
    "Dashboard": "Dashboard",
    "Struktura jednostek": "Unit structure",
    "Technologie": "Technologies",
    "Lista CVE": "CVE list",
    "Stan konfiguracji": "Configuration status",
    "Błędy": "Errors",
    "zakończona przez operatora": "ended by the operator",
    "zakończona przez Twoją organizację": "ended by your organization",
    "zakończona przez przełożonego supportu Forvium": "ended by a Forvium support supervisor",
    "zgoda została cofnięta": "the consent was revoked",
    "zgoda wygasła": "the consent expired",
    "upłynął czas sesji": "the session time ran out",
    "zgłoszenie zostało zamknięte": "the ticket was closed",
    "zakończona automatycznie przez system bezpieczeństwa Forvium":
        "ended automatically by the Forvium security system",
    "Czas trwania: {minutes} min {seconds} s": "Duration: {minutes} min {seconds} s",
    "Powód zakończenia: {reason}": "End reason: {reason}",
    "Liczba operacji (tylko odczyt): {n}": "Operations (read-only): {n}",
    "Zablokowane próby: {n}": "Blocked attempts: {n}",
    "Oglądane widoki: {views}": "Views opened: {views}",
    "brak": "none",
}
