<?php

/**
 * Przykładowe wpisy na blogu. Edytowalne później w panelu /cloudsecurepanel/articles.
 */

return [
    [
        'title'   => 'Zasada 3-2-1 backupu - dlaczego jedna kopia to zawsze za mało',
        'slug'    => 'zasada-3-2-1-backupu',
        'excerpt' => 'Trzy kopie danych, dwa różne nośniki, jedna kopia poza siedzibą firmy - jak w praktyce wdrożyć klasyczną zasadę backupu, która wciąż ratuje firmy przed utratą danych.',
        'content' => '<p>Zasada 3-2-1 to jeden z najstarszych, a zarazem wciąż najskuteczniejszych fundamentów strategii backupu. Mówi ona: utrzymuj co najmniej <strong>3 kopie</strong> danych, na <strong>2 różnych nośnikach</strong>, z czego <strong>1 kopia</strong> powinna znajdować się poza siedzibą firmy.</p><h2>Dlaczego jedna kopia nie wystarczy</h2><p>Firmy często zakładają, że skoro dane są "gdzieś zbackupowane", są bezpieczne. W praktyce pojedyncza kopia backupu przechowywana w tej samej serwerowni co dane produkcyjne jest podatna na te same zagrożenia: pożar, zalanie, kradzież sprzętu czy atak ransomware, który szyfruje wszystko w zasięgu sieci.</p><h2>Jak to wygląda w praktyce</h2><ul><li>Kopia produkcyjna (dane żywe)</li><li>Kopia lokalna na osobnym nośniku/repozytorium</li><li>Kopia poza siedzibą (off-site) lub w chmurze</li></ul><p>Coraz częściej dodaje się też zasadę "1 niezmienna" (immutable) - kopię, której nie da się usunąć ani zaszyfrować nawet z uprawnieniami administratora.</p>',
    ],
    [
        'title'   => 'Ransomware atakuje też backupy - jak się przed tym bronić',
        'slug'    => 'ransomware-atakuje-backupy',
        'excerpt' => 'Współczesne ataki ransomware coraz częściej celują bezpośrednio w repozytoria backupu. Sprawdź, jakie mechanizmy realnie chronią Twoje kopie zapasowe przed zaszyfrowaniem.',
        'content' => '<p>Przez lata backup był traktowany jako ostatnia linia obrony przed ransomware - jeśli dane produkcyjne zostały zaszyfrowane, wystarczyło odtworzyć je z kopii zapasowej. Współczesne ataki zmieniły tę zasadę gry.</p><h2>Nowa taktyka atakujących</h2><p>Zaawansowane grupy ransomware najpierw przez tygodnie penetrują sieć ofiary, identyfikując infrastrukturę backupu, a dopiero potem uruchamiają szyfrowanie - obejmujące również repozytoria kopii zapasowych i konsole zarządzające.</p><h2>Co realnie działa</h2><ul><li>Kopie niezmienne (immutable) - danych nie da się nadpisać ani usunąć w oknie retencji</li><li>Oddzielne, ograniczone konta dostępowe do systemu backupu</li><li>Segmentacja sieci między produkcją a infrastrukturą backupu</li><li>Regularne, rzeczywiste testy odtwarzania</li></ul><p>Backup bez tych mechanizmów to w najlepszym razie dodatkowe opóźnienie dla atakującego, a nie realna ochrona.</p>',
    ],
    [
        'title'   => 'RTO i RPO - dwie liczby, które decydują o przetrwaniu firmy po awarii',
        'slug'    => 'rto-i-rpo-wyjasnione',
        'excerpt' => 'Recovery Time Objective i Recovery Point Objective to podstawowe metryki każdego planu disaster recovery. Wyjaśniamy, co oznaczają i jak je wyznaczyć dla swojej firmy.',
        'content' => '<p>Każda strategia disaster recovery opiera się na dwóch kluczowych parametrach: RTO i RPO. Zrozumienie ich różnicy to pierwszy krok do zaprojektowania planu odtwarzania, który rzeczywiście odpowiada potrzebom biznesu.</p><h2>RTO - Recovery Time Objective</h2><p>To maksymalny akceptowalny czas, w jakim system musi zostać przywrócony do działania po awarii. Jeśli RTO wynosi 4 godziny, oznacza to, że po 4 godzinach od wystąpienia awarii kluczowe systemy muszą już działać.</p><h2>RPO - Recovery Point Objective</h2><p>To maksymalna akceptowalna ilość danych, jaką firma może utracić, liczona w czasie od ostatniej kopii zapasowej. RPO wynoszące 1 godzinę oznacza, że w najgorszym wypadku stracisz dane z ostatniej godziny przed awarią.</p><h2>Jak wyznaczyć właściwe wartości</h2><p>Nie każdy system w firmie wymaga tego samego poziomu ochrony. System sprzedażowy może wymagać RTO liczonego w minutach, podczas gdy archiwum dokumentów może tolerować RTO liczone w dniach. Dopasowanie RTO/RPO do realnej wartości biznesowej systemu pozwala zoptymalizować koszty ochrony.</p>',
    ],
];
