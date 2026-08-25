<?php

/**
 * Przykladowe wpisy na blogu. Edytowalne pozniej w panelu /cloudsecurepanel/articles.
 */

return [
    [
        'title'   => 'Zasada 3-2-1 backupu - dlaczego jedna kopia to zawsze za malo',
        'slug'    => 'zasada-3-2-1-backupu',
        'excerpt' => 'Trzy kopie danych, dwa rozne nosniki, jedna kopia poza siedziba firmy - jak w praktyce wdrozyc klasyczna zasade backupu, ktora wciaz ratuje firmy przed utrata danych.',
        'content' => '<p>Zasada 3-2-1 to jeden z najstarszych, a zarazem wciaz najskuteczniejszych fundamentow strategii backupu. Mowi ona: utrzymuj co najmniej <strong>3 kopie</strong> danych, na <strong>2 roznych nosnikach</strong>, z czego <strong>1 kopia</strong> powinna znajdowac sie poza siedziba firmy.</p><h2>Dlaczego jedna kopia nie wystarczy</h2><p>Firmy czesto zaklada, ze skoro dane sa "gdzies zbackupowane", sa bezpieczne. W praktyce pojedyncza kopia backupu przechowywana w tej samej serwerowni co dane produkcyjne jest podatna na te same zagrozenia: pozar, zalanie, kradziez sprzetu czy atak ransomware, ktory szyfruje wszystko w zasiegu sieci.</p><h2>Jak to wyglada w praktyce</h2><ul><li>Kopia produkcyjna (dane zywe)</li><li>Kopia lokalna na osobnym nosniku/repozytorium</li><li>Kopia poza siedziba (off-site) lub w chmurze</li></ul><p>Coraz czesciej dodaje sie tez zasade "1 niezmienna" (immutable) - kopie, ktorej nie da sie usunac ani zaszyfrowac nawet z uprawnieniami administratora.</p>',
    ],
    [
        'title'   => 'Ransomware atakuje tez backupy - jak sie przed tym bronic',
        'slug'    => 'ransomware-atakuje-backupy',
        'excerpt' => 'Wspolczesne ataki ransomware coraz czesciej celuja bezposrednio w repozytoria backupu. Sprawdz, jakie mechanizmy realnie chronia Twoje kopie zapasowe przed zaszyfrowaniem.',
        'content' => '<p>Przez lata backup byl traktowany jako ostatnia linia obrony przed ransomware - jesli dane produkcyjne zostaly zaszyfrowane, wystarczylo odtworzyc je z kopii zapasowej. Wspolczesne ataki zmienily te zasade gry.</p><h2>Nowa taktyka atakujacych</h2><p>Zaawansowane grupy ransomware najpierw przez tygodnie penetrowa siec ofiary, identyfikujac infrastrukture backupu, a dopiero potem uruchamiaja szyfrowanie - obejmujace rowniez repozytoria kopii zapasowych i konsole zarzadzajace.</p><h2>Co realnie dziala</h2><ul><li>Kopie niezmienne (immutable) - danych nie da sie nadpisac ani usunac w oknie retencji</li><li>Oddzielne, ograniczone konta dostepowe do systemu backupu</li><li>Segmentacja sieci miedzy produkcja a infrastruktura backupu</li><li>Regularne, rzeczywiste testy odtwarzania</li></ul><p>Backup bez tych mechanizmow to w najlepszym razie dodatkowe opoznienie dla atakujacego, a nie realna ochrona.</p>',
    ],
    [
        'title'   => 'RTO i RPO - dwie liczby, ktore decyduja o przetrwaniu firmy po awarii',
        'slug'    => 'rto-i-rpo-wyjasnione',
        'excerpt' => 'Recovery Time Objective i Recovery Point Objective to podstawowe metryki kazdego planu disaster recovery. Wyjasniamy, co oznaczaja i jak je wyznaczyc dla swojej firmy.',
        'content' => '<p>Kazda strategia disaster recovery opiera sie na dwoch kluczowych parametrach: RTO i RPO. Zrozumienie ich roznicy to pierwszy krok do zaprojektowania planu odtwarzania, ktory rzeczywiscie odpowiada potrzebom biznesu.</p><h2>RTO - Recovery Time Objective</h2><p>To maksymalny akceptowalny czas, w jakim system musi zostac przywrocony do dzialania po awarii. Jesli RTO wynosi 4 godziny, oznacza to, ze po 4 godzinach od wystapienia awarii kluczowe systemy musza juz dzialac.</p><h2>RPO - Recovery Point Objective</h2><p>To maksymalna akceptowalna ilosc danych, jaka firma moze utracic, liczona w czasie od ostatniej kopii zapasowej. RPO wynoszace 1 godzine oznacza, ze w najgorszym wypadku stracisz dane z ostatniej godziny przed awaria.</p><h2>Jak wyznaczyc wlasciwe wartosci</h2><p>Nie kazdy system w firmie wymaga tego samego poziomu ochrony. System sprzedazowy moze wymagac RTO liczonego w minutach, podczas gdy archiwum dokumentow moze tolerowac RTO liczone w dniach. Dopasowanie RTO/RPO do realnej wartosci biznesowej systemu pozwala zoptymalizowac koszty ochrony.</p>',
    ],
];
