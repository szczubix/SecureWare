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
            <h1 class="sw-anim-in sw-delay-2">Backup, który <span>działa</span>, gdy najbardziej go potrzebujesz</h1>
            <p class="lead sw-anim-in sw-delay-3">Zarządzany backup, ochrona przed ransomware i disaster recovery dla firm, które nie mogą sobie pozwolić na utratę danych. Monitorujemy, testujemy i raportujemy — 24/7.</p>
            <div class="sw-hero__actions sw-anim-in sw-delay-4">
                <a href="/kontakt" class="sw-btn sw-btn--primary">Umów bezpłatną konsultację</a>
                <a href="/oferta" class="sw-btn sw-btn--ghost">Zobacz ofertę <?= Icons::svg('arrow-right', 16) ?></a>
            </div>
            <div class="sw-hero__specs sw-anim-in sw-delay-5">
                <div><strong data-count="7" data-suffix=" lat">0 lat</strong><span>Doświadczenia w branży backupu</span></div>
                <div><strong>3-2-1-1-0</strong><span>Zasada ochrony danych</span></div>
                <div><strong>Immutable</strong><span>Kopie odporne na ransomware</span></div>
                <div><strong>24/7</strong><span>Monitoring i reakcja</span></div>
            </div>
        </div>
        <div class="sw-anim-in sw-delay-3">
            <div class="sw-diagram-card">
                <div class="sw-diagram-card__head">
                    <h3>Zasada 3-2-1-1-0 w praktyce</h3>
                    <span class="sw-diagram-card__live">Monitorowane 24/7</span>
                </div>
                <svg class="sw-diagram" viewBox="0 0 480 380" xmlns="http://www.w3.org/2000/svg">
                    <path class="flow" d="M240,72 L240,140"/>
                    <path class="flow" d="M240,196 C240,240 140,240 140,280"/>
                    <path class="flow" d="M240,196 C240,240 340,240 340,280"/>

                    <g class="node primary">
                        <rect x="160" y="16" width="160" height="56" rx="10"/>
                        <svg class="icon" x="176" y="30" width="22" height="22"><?= Icons::svg('server', 22) ?></svg>
                        <text x="210" y="40">Dane</text>
                        <text x="210" y="56" class="sub">produkcyjne</text>
                    </g>

                    <g class="node">
                        <rect x="160" y="140" width="160" height="56" rx="10"/>
                        <svg class="icon" x="176" y="154" width="22" height="22"><?= Icons::svg('layers', 22) ?></svg>
                        <text x="210" y="164">Kopia lokalna</text>
                        <text x="210" y="180" class="sub">inny nośnik</text>
                    </g>

                    <g class="node">
                        <rect x="60" y="280" width="160" height="70" rx="10"/>
                        <svg class="icon" x="76" y="296" width="20" height="20"><?= Icons::svg('cloud-upload', 20) ?></svg>
                        <text x="106" y="309">Kopia offsite</text>
                        <text x="106" y="325" class="sub">poza siedzibą</text>
                        <g class="verified" transform="translate(206,282)">
                            <circle r="10"/>
                            <svg x="-6" y="-6" width="12" height="12"><?= Icons::svg('check', 12) ?></svg>
                        </g>
                    </g>

                    <g class="node">
                        <rect x="260" y="280" width="160" height="70" rx="10"/>
                        <svg class="icon" x="276" y="296" width="20" height="20"><?= Icons::svg('lock', 20) ?></svg>
                        <text x="306" y="309">Immutable</text>
                        <text x="306" y="325" class="sub">offline / niezmienna</text>
                        <g class="verified" transform="translate(406,282)">
                            <circle r="10"/>
                            <svg x="-6" y="-6" width="12" height="12"><?= Icons::svg('check', 12) ?></svg>
                        </g>
                    </g>
                </svg>
                <div class="sw-diagram-card__foot">0 błędów — każda kopia jest testowana i weryfikowana</div>
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
            <h2>Pełen zakres ochrony danych</h2>
            <p>Od zarządzania istniejącym backupem po disaster recovery i cykliczne testy odtwarzania.</p>
        </div>
        <div class="sw-services-grid reveal-stagger">
            <?php foreach ($teaser as $s): ?>
                <div class="sw-service-card">
                    <div class="sw-service-card__icon"><?= Icons::svg($s['icon'], 22) ?></div>
                    <h3><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></h3>
                    <p><?= htmlspecialchars($s['short_description'], ENT_QUOTES, 'UTF-8') ?></p>
                    <a class="more" href="/oferta/<?= htmlspecialchars($s['slug'], ENT_QUOTES, 'UTF-8') ?>">Dowiedz się więcej <?= Icons::svg('arrow-right', 14) ?></a>
                </div>
            <?php endforeach; ?>
        </div>
        <div class="reveal" style="text-align:center;margin-top:36px;">
            <a href="/oferta" class="sw-btn sw-btn--dark">Zobacz pełną ofertę (13 usług)</a>
        </div>
    </div>
</section>

<section class="sw-section sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-stats-band reveal">
            <div class="sw-stats reveal-stagger reveal-stagger--pop">
                <div><strong data-count="7" data-suffix=" lat">0 lat</strong><span>Doświadczenia w branży backupu</span></div>
                <div><strong>24/7</strong><span>Monitoring środowisk backupu</span></div>
                <div><strong>&lt; 1h</strong><span>Docelowy czas reakcji na incydent</span></div>
                <div><strong data-count="100" data-suffix="%">0%</strong><span>Testowane, nie zakładane</span></div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Jak działamy</h5>
            <h2>Trzy filary pełnej ochrony danych</h2>
            <p>Backup, disaster recovery i monitoring — na tym opieramy każde wdrożenie, od pierwszej kopii po pełne disaster recovery.</p>
        </div>
        <div class="sw-platform reveal">
            <div class="sw-platform__tabs" role="tablist">
                <button type="button" class="sw-platform__tab is-active" data-tab="backup" role="tab" aria-selected="true">
                    <span class="icon"><?= Icons::svg('cloud-upload', 20) ?></span>
                    <span><strong>Backup i ochrona</strong><small>Kopie niezmienne, zgodne z 3-2-1-1-0</small></span>
                </button>
                <button type="button" class="sw-platform__tab" data-tab="dr" role="tab" aria-selected="false">
                    <span class="icon"><?= Icons::svg('life-buoy', 20) ?></span>
                    <span><strong>Disaster Recovery</strong><small>Procedury i cele RTO/RPO</small></span>
                </button>
                <button type="button" class="sw-platform__tab" data-tab="monitoring" role="tab" aria-selected="false">
                    <span class="icon"><?= Icons::svg('activity', 20) ?></span>
                    <span><strong>Monitoring i zgodność</strong><small>Nadzór 24/7 i raporty</small></span>
                </button>
            </div>
            <div class="sw-platform__panels">
                <div class="sw-platform__panel is-active" data-panel="backup">
                    <h3>Backup, który przetrwa atak</h3>
                    <p>Kopie w repozytorium niezmiennym (immutable), zgodne z zasadą 3-2-1-1-0 - dane pozostają odzyskiwalne nawet po przejęciu konta administratora.</p>
                    <ul>
                        <li><?= Icons::svg('check', 14) ?> Codzienne, automatyczne kopie bez ingerencji Twojego zespołu IT</li>
                        <li><?= Icons::svg('check', 14) ?> Wsparcie dla narzędzi, które już masz (np. Veeam, Proxmox Backup Server)</li>
                        <li><?= Icons::svg('check', 14) ?> Repozytoria immutable odporne na ransomware</li>
                    </ul>
                </div>
                <div class="sw-platform__panel" data-panel="dr">
                    <h3>Disaster Recovery zaplanowany, nie improwizowany</h3>
                    <p>Ustalamy z Tobą realne cele RTO/RPO i budujemy procedury, dzięki którym w razie awarii wiadomo dokładnie, co robić - krok po kroku.</p>
                    <ul>
                        <li><?= Icons::svg('check', 14) ?> Zdefiniowane cele czasu i punktu przywrócenia (RTO/RPO)</li>
                        <li><?= Icons::svg('check', 14) ?> Infrastruktura zapasowa gotowa do szybkiego przełączenia</li>
                        <li><?= Icons::svg('check', 14) ?> Spisana procedura awaryjna zamiast działania na pamięć</li>
                    </ul>
                </div>
                <div class="sw-platform__panel" data-panel="monitoring">
                    <h3>Nadzór, który nie śpi</h3>
                    <p>Środowisko backupu jest monitorowane całodobowo - reagujemy, zanim niepowodzenie kopii stanie się utratą danych.</p>
                    <ul>
                        <li><?= Icons::svg('check', 14) ?> Monitoring zadań backupu i repozytoriów 24/7</li>
                        <li><?= Icons::svg('check', 14) ?> Regularne, realne testy odtwarzania z raportem</li>
                        <li><?= Icons::svg('check', 14) ?> Polityki retencji zgodne z wymaganiami compliance</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Standard branżowy</h5>
            <h2>Zasada 3-2-1-1-0</h2>
            <p>Rozszerzenie klasycznej zasady 3-2-1 do 3-2-1-1-0, o ochronę przed ransomware i obowiązek regularnej weryfikacji kopii. Kliknij element, żeby zobaczyć szczegóły.</p>
        </div>
        <div class="sw-rule reveal">
            <svg class="sw-rule__line" viewBox="0 0 1000 24" preserveAspectRatio="none" aria-hidden="true">
                <path class="base" d="M0,12 H1000"/>
                <path class="flow" d="M0,12 H1000"/>
            </svg>
            <span class="sw-rule__packet" aria-hidden="true"></span>
            <div class="sw-rule__row reveal-stagger">
                <div class="sw-rule__item">
                    <button type="button" class="sw-rule__node" aria-expanded="false">
                        <span class="icon-badge"><?= Icons::svg('layers', 18) ?></span>
                        <span class="num">3</span>
                        <span class="label">Kopie danych</span>
                        <?= Icons::svg('chevron-down', 14) ?>
                    </button>
                    <div class="sw-rule__panel">
                        <p>Zawsze co najmniej trzy kopie: dane produkcyjne oraz dwie kopie zapasowe. Nawet jeśli jedna zawiedzie, pozostałe pozwalają odzyskać dane.</p>
                    </div>
                </div>
                <div class="sw-rule__item">
                    <button type="button" class="sw-rule__node" aria-expanded="false">
                        <span class="icon-badge"><?= Icons::svg('server', 18) ?></span>
                        <span class="num">2</span>
                        <span class="label">Rodzaje nośników</span>
                        <?= Icons::svg('chevron-down', 14) ?>
                    </button>
                    <div class="sw-rule__panel">
                        <p>Kopie przechowywane na dwóch różnych typach nośników (np. lokalny storage i chmura) - awaria jednego typu nośnika nie unieważnia wszystkich kopii naraz.</p>
                    </div>
                </div>
                <div class="sw-rule__item">
                    <button type="button" class="sw-rule__node" aria-expanded="false">
                        <span class="icon-badge"><?= Icons::svg('cloud-upload', 18) ?></span>
                        <span class="num">1</span>
                        <span class="label">Kopia offsite</span>
                        <?= Icons::svg('chevron-down', 14) ?>
                    </button>
                    <div class="sw-rule__panel">
                        <p>Co najmniej jedna kopia poza siedzibą firmy. Chroni dane przed zdarzeniami, które mogą zniszczyć całą lokalną infrastrukturę - pożarem, zalaniem, kradzieżą sprzętu.</p>
                    </div>
                </div>
                <div class="sw-rule__item">
                    <button type="button" class="sw-rule__node" aria-expanded="false">
                        <span class="icon-badge"><?= Icons::svg('lock', 18) ?></span>
                        <span class="num">1</span>
                        <span class="label">Offline / immutable</span>
                        <?= Icons::svg('chevron-down', 14) ?>
                    </button>
                    <div class="sw-rule__panel">
                        <p>Dodatkowa kopia odizolowana od sieci lub niezmienna (immutable) - odporna na ransomware, który celuje właśnie w systemy backupu, żeby odciąć drogę do odzyskania danych.</p>
                    </div>
                </div>
                <div class="sw-rule__item">
                    <button type="button" class="sw-rule__node" aria-expanded="false">
                        <span class="icon-badge"><?= Icons::svg('shield-check', 18) ?></span>
                        <span class="num">0</span>
                        <span class="label">Błędów w kopiach</span>
                        <?= Icons::svg('chevron-down', 14) ?>
                    </button>
                    <div class="sw-rule__panel">
                        <p>Kopie regularnie testowane i weryfikowane przez realne odtwarzanie danych - zero niespodzianek w momencie, w którym backup trzeba faktycznie użyć.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section sw-section--muted">
    <div class="sw-wrap sw-why">
        <div class="sw-why__intro reveal">
            <h5>Dlaczego SecureWare</h5>
            <h2>Backup, któremu można zaufać</h2>
            <p>Nie sprzedajemy licencji i nie znikamy po wdrożeniu — zarządzamy Twoim backupem tak, jakby był naszym własnym.</p>
            <a href="/kontakt" class="sw-why__link">Porozmawiajmy o Twoim środowisku <?= Icons::svg('arrow-right', 14) ?></a>
        </div>
        <div class="sw-why__list reveal-stagger">
            <div class="sw-why__item">
                <span class="num">01</span>
                <div>
                    <h4>Ochrona przed ransomware</h4>
                    <p>Kopie niezmienne i segmentacja infrastruktury backupu.</p>
                </div>
            </div>
            <div class="sw-why__item">
                <span class="num">02</span>
                <div>
                    <h4>Rzeczywiste testy</h4>
                    <p>Nie sprawdzamy tylko statusu zadania - realnie odtwarzamy dane.</p>
                </div>
            </div>
            <div class="sw-why__item">
                <span class="num">03</span>
                <div>
                    <h4>Nadzór 24/7</h4>
                    <p>Reagujemy, zanim problem stanie się awarią.</p>
                </div>
            </div>
            <div class="sw-why__item">
                <span class="num">04</span>
                <div>
                    <h4>Jasne raporty</h4>
                    <p>Zrozumiałe raporty również dla osób spoza IT.</p>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Jak to działa</h5>
            <h2>Wdrożenie krok po kroku</h2>
            <p>Bez wielomiesięcznych projektów - od pierwszej rozmowy do działającej ochrony danych.</p>
        </div>
        <div class="sw-steps reveal-stagger">
            <div class="sw-step">
                <span class="sw-step__num">1</span>
                <h4>Audyt i konsultacja</h4>
                <p>Analizujemy obecne środowisko, wymagania RTO/RPO i budżet, aby zaproponować rozwiązanie dopasowane do skali firmy.</p>
            </div>
            <div class="sw-step">
                <span class="sw-step__num">2</span>
                <h4>Wdrożenie</h4>
                <p>Konfigurujemy backup, repozytoria i polityki retencji - dla nowego środowiska lub w oparciu o narzędzia, które już posiadasz.</p>
            </div>
            <div class="sw-step">
                <span class="sw-step__num">3</span>
                <h4>Monitoring i testy</h4>
                <p>Nadzorujemy środowisko 24/7 i regularnie testujemy rzeczywiste odtwarzanie danych - z raportem po każdym teście.</p>
            </div>
        </div>
    </div>
</section>

<?php if ($latestArticles): ?>
<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5>Z bloga</h5>
            <h2>Najnowsze artykuły</h2>
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
            <h2>Najczęściej zadawane pytania</h2>
        </div>
        <div class="sw-faq reveal">
            <details open>
                <summary>Czym różni się backup od disaster recovery?</summary>
                <p>Backup pozwala odzyskać dane. Disaster recovery pozwala odzyskać działanie firmy - obejmuje procedury, infrastrukturę zapasową oraz zdefiniowane cele RTO/RPO, dzięki którym wiadomo, jak szybko i z jaką stratą danych systemy wrócą do pracy.</p>
            </details>
            <details>
                <summary>Czy mogę zachować obecne oprogramowanie do backupu?</summary>
                <p>Tak. W ramach Managed Backup przejmujemy nadzór nad środowiskiem, które już masz (np. Veeam, Proxmox Backup Server). Migracja na nową platformę jest opcjonalna, nie warunkiem współpracy.</p>
            </details>
            <details>
                <summary>Ile trwa wdrożenie?</summary>
                <p>Zależy od skali środowiska - prosty Backup as a Service można uruchomić w ciągu kilku dni, pełne wdrożenie z disaster recovery i testami odtwarzania zwykle zajmuje kilka tygodni.</p>
            </details>
            <details>
                <summary>Co dzieje się w razie ataku ransomware?</summary>
                <p>Kopie w repozytorium niezmiennym (immutable) pozostają nienaruszone nawet po przejęciu konta administratora, co pozwala odtworzyć dane bez płacenia okupu. Reagujemy w ramach procedury disaster recovery ustalonej wcześniej z Tobą.</p>
            </details>
            <details>
                <summary>Czy oferujecie bezpłatną konsultację?</summary>
                <p>Tak - pierwsza rozmowa i wstępny przegląd obecnego środowiska backupu są bezpłatne. Umów ją przez formularz kontaktowy.</p>
            </details>
        </div>
    </div>
</section>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2>Nie wiesz, czy Twój backup naprawdę zadziała?</h2>
                <p>Zamów bezpłatny audyt obecnego środowiska ochrony danych.</p>
            </div>
            <a href="/kontakt" class="sw-btn sw-btn--dark">Zamów audyt</a>
        </div>
    </div>
</section>
