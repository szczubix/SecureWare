<?php
/** @var array $services */
/** @var array $latestArticles */
use SecureWare\Core\Icons;
use SecureWare\Core\Str;

$teaser = array_slice($services, 0, 6);
?>
<section class="sw-hero">
    <div class="sw-wrap sw-hero__grid">
        <div>
            <span class="sw-hero__eyebrow sw-anim-in sw-delay-1">Backup &amp; Disaster Recovery</span>
            <h1 class="sw-anim-in sw-delay-2">Backup, ktory <span>dziala</span>, gdy najbardziej go potrzebujesz</h1>
            <p class="lead sw-anim-in sw-delay-3">Zarzadzany backup, ochrona przed ransomware i disaster recovery dla firm, ktore nie moga sobie pozwolic na utrate danych. Monitorujemy, testujemy i raportujemy — 24/7.</p>
            <div class="sw-hero__actions sw-anim-in sw-delay-4">
                <a href="/kontakt" class="sw-btn sw-btn--primary">Umow bezplatna konsultacje</a>
                <a href="/oferta" class="sw-btn sw-btn--ghost">Zobacz oferte <?= Icons::svg('arrow-right', 16) ?></a>
            </div>
            <div class="sw-hero__badges sw-anim-in sw-delay-5">
                <span>✔ Zgodnosc z zasada 3-2-1</span>
                <span>✔ Kopie niezmienne (immutable)</span>
                <span>✔ Testy odtwarzania</span>
            </div>
        </div>
        <div class="sw-hero__mockwrap sw-anim-in sw-delay-3">
            <div class="sw-mock__badge sw-mock__badge--tl">
                <span class="icon"><?= Icons::svg('shield-check', 16) ?></span> Ransomware-safe
            </div>
            <div class="sw-mock">
                <div class="sw-mock__bar">
                    <span class="sw-mock__dot"></span><span class="sw-mock__dot"></span><span class="sw-mock__dot"></span>
                    <span>Panel ochrony danych</span>
                </div>
                <div class="sw-mock__body">
                    <div class="sw-mock__headline">
                        <strong data-count="247" data-suffix=" TB">0 TB</strong>
                        <span class="sw-mock__live">na żywo</span>
                    </div>
                    <div class="sw-mock__bars">
                        <i style="animation-delay:-0.2s;height:38%"></i>
                        <i style="animation-delay:-1.6s;height:62%"></i>
                        <i style="animation-delay:-0.8s;height:48%"></i>
                        <i style="animation-delay:-2.1s;height:82%"></i>
                        <i style="animation-delay:-0.4s;height:58%"></i>
                        <i style="animation-delay:-1.2s;height:70%"></i>
                        <i style="animation-delay:-1.9s;height:44%"></i>
                    </div>
                    <div class="sw-mock__rows">
                        <div class="sw-mock__row">
                            <span class="ok"><?= Icons::svg('check', 12) ?></span>
                            <span class="label">Backup nocny</span><span class="val">OK · 02:14</span>
                        </div>
                        <div class="sw-mock__row">
                            <span class="ok"><?= Icons::svg('check', 12) ?></span>
                            <span class="label">Test odtwarzania</span><span class="val">OK · wczoraj</span>
                        </div>
                        <div class="sw-mock__row">
                            <span class="ok"><?= Icons::svg('check', 12) ?></span>
                            <span class="label">Repozytorium immutable</span><span class="val">Aktywne</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="sw-mock__badge sw-mock__badge--br">
                <span class="icon"><?= Icons::svg('activity', 16) ?></span> Monitoring 24/7
            </div>
        </div>
    </div>
</section>

<div class="sw-ticker" aria-hidden="true">
    <div class="sw-ticker__track">
        <?php foreach (array_merge($services, $services) as $s): ?>
            <span><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></span>
        <?php endforeach; ?>
    </div>
</div>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Nasza oferta</h5>
            <h2>Pelen zakres ochrony danych</h2>
            <p>Od zarzadzania istniejacym backupem po disaster recovery i cykliczne testy odtwarzania.</p>
        </div>
        <div class="sw-services-grid reveal-stagger">
            <?php foreach ($teaser as $s): ?>
                <div class="sw-service-card">
                    <div class="sw-service-card__icon"><?= Icons::svg($s['icon'], 22) ?></div>
                    <h3><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></h3>
                    <p><?= htmlspecialchars($s['short_description'], ENT_QUOTES, 'UTF-8') ?></p>
                    <a class="more" href="/oferta/<?= htmlspecialchars($s['slug'], ENT_QUOTES, 'UTF-8') ?>">Dowiedz sie wiecej <?= Icons::svg('arrow-right', 14) ?></a>
                </div>
            <?php endforeach; ?>
        </div>
        <div class="reveal" style="text-align:center;margin-top:36px;">
            <a href="/oferta" class="sw-btn sw-btn--dark">Zobacz pelna oferte (13 uslug)</a>
        </div>
    </div>
</section>

<section class="sw-section sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-stats-band reveal">
            <div class="sw-stats reveal-stagger reveal-stagger--pop">
                <div><strong>24/7</strong><span>Monitoring srodowisk backupu</span></div>
                <div><strong>3-2-1</strong><span>Zasada ochrony danych, ktora dziala</span></div>
                <div><strong>&lt; 1h</strong><span>Docelowy czas reakcji na incydent</span></div>
                <div><strong>100%</strong><span>Testowane, nie zakladane</span></div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Platforma</h5>
            <h2>Jedna platforma, pelna ochrona danych</h2>
            <p>Trzy filary, na ktorych opieramy kazde wdrozenie — od pierwszej kopii po pelne disaster recovery.</p>
        </div>
        <div class="sw-platform reveal">
            <div class="sw-platform__tabs" role="tablist">
                <button type="button" class="sw-platform__tab is-active" data-tab="backup" role="tab" aria-selected="true">
                    <span class="icon"><?= Icons::svg('cloud-upload', 20) ?></span>
                    <span><strong>Backup i ochrona</strong><small>Kopie niezmienne, zgodne z 3-2-1</small></span>
                </button>
                <button type="button" class="sw-platform__tab" data-tab="dr" role="tab" aria-selected="false">
                    <span class="icon"><?= Icons::svg('life-buoy', 20) ?></span>
                    <span><strong>Disaster Recovery</strong><small>Procedury i cele RTO/RPO</small></span>
                </button>
                <button type="button" class="sw-platform__tab" data-tab="monitoring" role="tab" aria-selected="false">
                    <span class="icon"><?= Icons::svg('activity', 20) ?></span>
                    <span><strong>Monitoring i zgodnosc</strong><small>Nadzor 24/7 i raporty</small></span>
                </button>
            </div>
            <div class="sw-platform__panels">
                <div class="sw-platform__panel is-active" data-panel="backup">
                    <h3>Backup, ktory przetrwa atak</h3>
                    <p>Kopie w repozytorium niezmiennym (immutable), zgodne z zasada 3-2-1 - dane pozostaja odzyskiwalne nawet po przejeciu konta administratora.</p>
                    <ul>
                        <li><?= Icons::svg('check', 14) ?> Codzienne, automatyczne kopie bez ingerencji Twojego zespolu IT</li>
                        <li><?= Icons::svg('check', 14) ?> Wsparcie dla narzedzi, ktore juz masz (np. Veeam, Proxmox Backup Server)</li>
                        <li><?= Icons::svg('check', 14) ?> Repozytoria immutable odporne na ransomware</li>
                    </ul>
                </div>
                <div class="sw-platform__panel" data-panel="dr">
                    <h3>Disaster Recovery zaplanowany, nie improwizowany</h3>
                    <p>Ustalamy z Toba realne cele RTO/RPO i budujemy procedury, dzieki ktorym w razie awarii wiadomo dokladnie, co robic - krok po kroku.</p>
                    <ul>
                        <li><?= Icons::svg('check', 14) ?> Zdefiniowane cele czasu i punktu przywrocenia (RTO/RPO)</li>
                        <li><?= Icons::svg('check', 14) ?> Infrastruktura zapasowa gotowa do szybkiego przelaczenia</li>
                        <li><?= Icons::svg('check', 14) ?> Spisana procedura awaryjna zamiast dzialania na pamiec</li>
                    </ul>
                </div>
                <div class="sw-platform__panel" data-panel="monitoring">
                    <h3>Nadzor, ktory nie spi</h3>
                    <p>Srodowisko backupu jest monitorowane calodobowo - reagujemy zanim niepowodzenie kopii stanie sie utrata danych.</p>
                    <ul>
                        <li><?= Icons::svg('check', 14) ?> Monitoring zadan backupu i repozytoriow 24/7</li>
                        <li><?= Icons::svg('check', 14) ?> Regularne, realne testy odtwarzania z raportem</li>
                        <li><?= Icons::svg('check', 14) ?> Polityki retencji zgodne z wymaganiami compliance</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section sw-section--muted">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Dlaczego SecureWare</h5>
            <h2>Backup, ktoremu mozna zaufac</h2>
        </div>
        <div class="sw-why-grid reveal-stagger">
            <div>
                <div class="icon"><?= Icons::svg('shield-check', 24) ?></div>
                <h4>Ochrona przed ransomware</h4>
                <p>Kopie niezmienne i segmentacja infrastruktury backupu.</p>
            </div>
            <div>
                <div class="icon"><?= Icons::svg('refresh-ccw', 24) ?></div>
                <h4>Rzeczywiste testy</h4>
                <p>Nie sprawdzamy tylko statusu zadania - realnie odtwarzamy dane.</p>
            </div>
            <div>
                <div class="icon"><?= Icons::svg('activity', 24) ?></div>
                <h4>Nadzor 24/7</h4>
                <p>Reagujemy zanim problem stanie sie awaria.</p>
            </div>
            <div>
                <div class="icon"><?= Icons::svg('file-check', 24) ?></div>
                <h4>Jasne raporty</h4>
                <p>Zrozumiale raporty rowniez dla osob spoza IT.</p>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Jak to dziala</h5>
            <h2>Wdrozenie krok po kroku</h2>
            <p>Bez wielomiesiecznych projektow - od pierwszej rozmowy do dzialajacej ochrony danych.</p>
        </div>
        <div class="sw-steps reveal-stagger">
            <div class="sw-step">
                <span class="sw-step__num">1</span>
                <h4>Audyt i konsultacja</h4>
                <p>Analizujemy obecne srodowisko, wymagania RTO/RPO i budzet, aby zaproponowac rozwiazanie dopasowane do skali firmy.</p>
            </div>
            <div class="sw-step">
                <span class="sw-step__num">2</span>
                <h4>Wdrozenie</h4>
                <p>Konfigurujemy backup, repozytoria i polityki retencji - dla nowego srodowiska lub w oparciu o narzedzia, ktore juz posiadasz.</p>
            </div>
            <div class="sw-step">
                <span class="sw-step__num">3</span>
                <h4>Monitoring i testy</h4>
                <p>Nadzorujemy srodowisko 24/7 i regularnie testujemy rzeczywiste odtwarzanie danych - z raportem po kazdym tescie.</p>
            </div>
        </div>
    </div>
</section>

<?php if ($latestArticles): ?>
<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Z bloga</h5>
            <h2>Najnowsze artykuly</h2>
        </div>
        <div class="sw-blog-grid reveal-stagger">
            <?php foreach ($latestArticles as $a): ?>
                <a class="sw-blog-card" href="/blog/<?= htmlspecialchars($a['slug'], ENT_QUOTES, 'UTF-8') ?>">
                    <div class="sw-blog-card__img"><?php if ($a['featured_image_path']): ?><img src="<?= htmlspecialchars($a['featured_image_path'], ENT_QUOTES, 'UTF-8') ?>" alt=""><?php endif; ?></div>
                    <div class="sw-blog-card__body">
                        <span class="meta"><?= htmlspecialchars($a['category_name'] ?? 'Blog', ENT_QUOTES, 'UTF-8') ?></span>
                        <h3><?= htmlspecialchars($a['title'], ENT_QUOTES, 'UTF-8') ?></h3>
                        <p><?= htmlspecialchars(Str::excerpt($a['excerpt'] ?: $a['content'], 100), ENT_QUOTES, 'UTF-8') ?></p>
                    </div>
                </a>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endif; ?>

<section class="sw-section sw-section--muted">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Pytania</h5>
            <h2>Najczesciej zadawane pytania</h2>
        </div>
        <div class="sw-faq reveal">
            <details open>
                <summary>Czym rozni sie backup od disaster recovery?</summary>
                <p>Backup pozwala odzyskac dane. Disaster recovery pozwala odzyskac dzialanie firmy - obejmuje procedury, infrastrukture zapasowa oraz zdefiniowane cele RTO/RPO, dzieki ktorym wiadomo, jak szybko i z jaka strata danych systemy wroca do pracy.</p>
            </details>
            <details>
                <summary>Czy moge zachowac obecne oprogramowanie do backupu?</summary>
                <p>Tak. W ramach Managed Backup przejmujemy nadzor nad srodowiskiem, ktore juz masz (np. Veeam, Proxmox Backup Server). Migracja na nowa platforme jest opcjonalna, nie warunkiem wspolpracy.</p>
            </details>
            <details>
                <summary>Ile trwa wdrozenie?</summary>
                <p>Zalezy od skali srodowiska - prosty Backup as a Service mozna uruchomic w ciagu kilku dni, pelne wdrozenie z disaster recovery i testami odtwarzania zwykle zajmuje kilka tygodni.</p>
            </details>
            <details>
                <summary>Co dzieje sie w razie ataku ransomware?</summary>
                <p>Kopie w repozytorium niezmiennym (immutable) pozostaja nienaruszone nawet po przejeciu konta administratora, co pozwala odtworzyc dane bez placenia okupu. Reagujemy w ramach procedury disaster recovery ustalonej wczesniej z Toba.</p>
            </details>
            <details>
                <summary>Czy oferujecie bezplatna konsultacje?</summary>
                <p>Tak - pierwsza rozmowa i wstepny przeglad obecnego srodowiska backupu sa bezplatne. Umow ja przez formularz kontaktowy.</p>
            </details>
        </div>
    </div>
</section>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2>Nie wiesz, czy Twoj backup naprawde zadziala?</h2>
                <p>Zamow bezplatny audyt obecnego srodowiska ochrony danych.</p>
            </div>
            <a href="/kontakt" class="sw-btn sw-btn--dark">Zamow audyt</a>
        </div>
    </div>
</section>
