<?php
/** @var array $content */
/** @var string|null $saved */
/** @var string $lang */
use SecureWare\Core\Csrf;

$isEn = $lang === 'en';

$icons = ['shield-check','cloud-upload','map-pin','lock','mail','server','layers','life-buoy','refresh-ccw','clipboard-check','tool','activity','file-check','shield'];
$iconSelect = function (string $name, string $selected) use ($icons) {
    echo '<select name="' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '">';
    foreach ($icons as $icon) {
        $sel = $selected === $icon ? ' selected' : '';
        echo '<option value="' . $icon . '"' . $sel . '>' . $icon . '</option>';
    }
    echo '</select>';
};
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<div class="toolbar">
    <h1>Treść strony głównej</h1>
    <a href="<?= $isEn ? '/en' : '/' ?>" target="_blank" class="button button--ghost">Zobacz stronę ↗</a>
</div>

<div class="admin-lang-tabs">
    <a href="homepage" class="<?= !$isEn ? 'is-active' : '' ?>">Polski</a>
    <a href="homepage?lang=en" class="<?= $isEn ? 'is-active' : '' ?>">English (EN)</a>
</div>

<?php if ($saved): ?><p class="alert alert--success">Zapisano treść strony głównej<?= $isEn ? ' (EN)' : '' ?>.</p><?php endif; ?>
<p class="admin-hint" style="margin:-8px 0 20px;color:#6b7686;">Tu edytujesz każdy tekst widoczny na stronie głównej — bez zmian w kodzie. Puste pole = zostaje pominięte przy wyświetlaniu.</p>

<form method="post" action="homepage<?= $isEn ? '?lang=en' : '' ?>">
    <?= Csrf::field() ?>
    <?php if ($isEn): ?><input type="hidden" name="lang" value="en"><?php endif; ?>

    <div class="admin-card">
        <h2 style="margin-top:0;">Hero (nagłówek strony)</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow (mały nagłówek nad tytułem)</label><input type="text" name="hero_eyebrow" value="<?= $h($content['hero']['eyebrow']) ?>"></div>
            </div>
            <div class="form-row">
                <div class="field"><label>Tytuł — część przed wyróżnionym słowem</label><input type="text" name="hero_headline_pre" value="<?= $h($content['hero']['headline_pre']) ?>"></div>
                <div class="field"><label>Tytuł — wyróżnione słowo</label><input type="text" name="hero_headline_highlight" value="<?= $h($content['hero']['headline_highlight']) ?>"></div>
                <div class="field"><label>Tytuł — część po wyróżnionym słowie</label><input type="text" name="hero_headline_post" value="<?= $h($content['hero']['headline_post']) ?>"></div>
            </div>
            <div class="field"><label>Lead (akapit pod tytułem)</label><textarea name="hero_lead" rows="2"><?= $h($content['hero']['lead']) ?></textarea></div>
            <div class="form-row">
                <div class="field"><label>Przycisk główny — tekst</label><input type="text" name="hero_cta_primary_label" value="<?= $h($content['hero']['cta_primary_label']) ?>"></div>
                <div class="field"><label>Przycisk główny — adres</label><input type="text" name="hero_cta_primary_url" value="<?= $h($content['hero']['cta_primary_url']) ?>"></div>
            </div>
            <div class="form-row">
                <div class="field"><label>Przycisk drugi — tekst</label><input type="text" name="hero_cta_secondary_label" value="<?= $h($content['hero']['cta_secondary_label']) ?>"></div>
                <div class="field"><label>Przycisk drugi — adres</label><input type="text" name="hero_cta_secondary_url" value="<?= $h($content['hero']['cta_secondary_url']) ?>"></div>
            </div>

            <h3>Cztery liczby pod przyciskami</h3>
            <?php foreach ($content['hero']['specs'] as $i => $spec): ?>
                <div class="form-row">
                    <div class="field"><label>Pozycja <?= $i + 1 ?> — liczba do animacji (puste = bez animacji)</label><input type="number" name="hero_spec_count[]" value="<?= $h($spec['count']) ?>"></div>
                    <div class="field"><label>Sufiks po liczbie (np. " lat")</label><input type="text" name="hero_spec_suffix[]" value="<?= $h($spec['suffix']) ?>"></div>
                    <div class="field"><label>Wartość tekstowa (gdy bez animacji, np. "24/7")</label><input type="text" name="hero_spec_value[]" value="<?= $h($spec['value']) ?>"></div>
                    <div class="field"><label>Opis pod wartością</label><input type="text" name="hero_spec_label[]" value="<?= $h($spec['label']) ?>"></div>
                </div>
            <?php endforeach; ?>

            <h3>Karta diagramu 3-2-1-1-0</h3>
            <div class="form-row">
                <div class="field"><label>Tytuł karty</label><input type="text" name="hero_diagram_title" value="<?= $h($content['hero']['diagram_title']) ?>"></div>
                <div class="field"><label>Odznaka "na żywo"</label><input type="text" name="hero_diagram_badge" value="<?= $h($content['hero']['diagram_badge']) ?>"></div>
            </div>
            <div class="field"><label>Stopka karty</label><input type="text" name="hero_diagram_foot" value="<?= $h($content['hero']['diagram_foot']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Nasza oferta"</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="offer_eyebrow" value="<?= $h($content['offer']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="offer_heading" value="<?= $h($content['offer']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="offer_intro" rows="2"><?= $h($content['offer']['intro']) ?></textarea></div>
            <div class="field"><label>Tekst przycisku "zobacz pełną ofertę"</label><input type="text" name="offer_cta_label" value="<?= $h($content['offer']['cta_label']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Pasek "Integrujemy się z"</h2>
        <div class="form-grid form-grid--wide">
            <div class="field"><label>Etykieta nad paskiem</label><input type="text" name="stack_eyebrow" value="<?= $h($content['stack']['eyebrow']) ?>"></div>
            <div class="field"><label>Nazwy narzędzi/technologii (jedna na linię)</label><textarea name="stack_items" rows="5"><?= $h($content['stack']['items']) ?></textarea><span class="hint">Pokazuje się jako pasek zaufania zaraz pod hero. Wpisuj tylko realne technologie, z którymi faktycznie współpracujecie.</span></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Pasek statystyk</h2>
        <div class="form-grid form-grid--wide">
            <?php foreach ($content['stats']['items'] as $i => $stat): ?>
                <div class="form-row">
                    <div class="field"><label>Statystyka <?= $i + 1 ?> — liczba do animacji</label><input type="number" name="stats_count[]" value="<?= $h($stat['count']) ?>"></div>
                    <div class="field"><label>Sufiks</label><input type="text" name="stats_suffix[]" value="<?= $h($stat['suffix']) ?>"></div>
                    <div class="field"><label>Wartość tekstowa</label><input type="text" name="stats_value[]" value="<?= $h($stat['value']) ?>"></div>
                    <div class="field"><label>Opis</label><input type="text" name="stats_label[]" value="<?= $h($stat['label']) ?>"></div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Jak działamy" (zakładki)</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="platform_eyebrow" value="<?= $h($content['platform']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="platform_heading" value="<?= $h($content['platform']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="platform_intro" rows="2"><?= $h($content['platform']['intro']) ?></textarea></div>

            <?php foreach ($content['platform']['tabs'] as $i => $tab): ?>
                <h3>Zakładka <?= $i + 1 ?></h3>
                <div class="form-row">
                    <div class="field"><label>Ikona</label><?php $iconSelect('platform_tab_icon[]', $tab['icon']); ?></div>
                    <div class="field"><label>Tytuł zakładki</label><input type="text" name="platform_tab_title[]" value="<?= $h($tab['title']) ?>"></div>
                    <div class="field"><label>Podtytuł zakładki</label><input type="text" name="platform_tab_subtitle[]" value="<?= $h($tab['subtitle']) ?>"></div>
                </div>
                <div class="field"><label>Tytuł panelu</label><input type="text" name="platform_tab_panel_title[]" value="<?= $h($tab['panel_title']) ?>"></div>
                <div class="field"><label>Tekst panelu</label><textarea name="platform_tab_panel_text[]" rows="2"><?= $h($tab['panel_text']) ?></textarea></div>
                <div class="field"><label>Punkty listy (jeden na linię)</label><textarea name="platform_tab_bullets[]" rows="3"><?= $h($tab['bullets']) ?></textarea></div>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Zasada 3-2-1-1-0"</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="rule_eyebrow" value="<?= $h($content['rule']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="rule_heading" value="<?= $h($content['rule']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="rule_intro" rows="2"><?= $h($content['rule']['intro']) ?></textarea></div>

            <?php foreach ($content['rule']['items'] as $i => $item): ?>
                <h3>Element <?= $i + 1 ?></h3>
                <div class="form-row">
                    <div class="field"><label>Ikona</label><?php $iconSelect('rule_item_icon[]', $item['icon']); ?></div>
                    <div class="field"><label>Cyfra (np. "3", "1", "0")</label><input type="text" name="rule_item_num[]" value="<?= $h($item['num']) ?>"></div>
                    <div class="field"><label>Etykieta</label><input type="text" name="rule_item_label[]" value="<?= $h($item['label']) ?>"></div>
                </div>
                <div class="field"><label>Opis (po rozwinięciu)</label><textarea name="rule_item_text[]" rows="2"><?= $h($item['text']) ?></textarea></div>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Ransomware kontra 3-2-1-1-0" (animacja)</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="ransomware_eyebrow" value="<?= $h($content['ransomware']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="ransomware_heading" value="<?= $h($content['ransomware']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="ransomware_intro" rows="2"><?= $h($content['ransomware']['intro']) ?></textarea></div>
            <div class="field"><label>Etykieta przy kopii immutable</label><input type="text" name="ransomware_protected_label" value="<?= $h($content['ransomware']['protected_label']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Dwa scenariusze ataku" (animacja)</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="scenario_eyebrow" value="<?= $h($content['scenario']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="scenario_heading" value="<?= $h($content['scenario']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="scenario_intro" rows="2"><?= $h($content['scenario']['intro']) ?></textarea></div>

            <h3>Panel zagrożenia (bez immutable)</h3>
            <div class="field"><label>Odznaka</label><input type="text" name="scenario_threat_badge" value="<?= $h($content['scenario']['threat_badge']) ?>"></div>
            <div class="field"><label>Linie wiadomości okupu (jedna na linię)</label><textarea name="scenario_threat_lines" rows="3"><?= $h($content['scenario']['threat_lines']) ?></textarea></div>
            <div class="form-row">
                <div class="field"><label>Kwota okupu (liczba)</label><input type="number" name="scenario_threat_amount" value="<?= $h($content['scenario']['threat_amount']) ?>"></div>
                <div class="field"><label>Sufiks (np. " zł")</label><input type="text" name="scenario_threat_suffix" value="<?= $h($content['scenario']['threat_suffix']) ?>"></div>
            </div>
            <div class="field"><label>Termin</label><input type="text" name="scenario_threat_deadline" value="<?= $h($content['scenario']['threat_deadline']) ?>"></div>

            <h3>Panel bezpieczeństwa (z immutable)</h3>
            <div class="field"><label>Odznaka</label><input type="text" name="scenario_safe_badge" value="<?= $h($content['scenario']['safe_badge']) ?>"></div>
            <div class="field"><label>Wstęp</label><input type="text" name="scenario_safe_intro" value="<?= $h($content['scenario']['safe_intro']) ?>"></div>
            <div class="field"><label>Lista kontrolna (jedna pozycja na linię)</label><textarea name="scenario_safe_checklist" rows="3"><?= $h($content['scenario']['safe_checklist']) ?></textarea></div>
            <div class="field"><label>Wynik końcowy</label><input type="text" name="scenario_safe_result" value="<?= $h($content['scenario']['safe_result']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Pasek "Kalkulator kosztu przestoju"</h2>
        <p class="hint" style="margin-top:-6px;">Link do narzędzia wskazuje zawsze na /kalkulator-kosztu-przestoju - nieedytowalny, żeby nie dało się go przypadkiem zepsuć.</p>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="calc_promo_eyebrow" value="<?= $h($content['calc_promo']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="calc_promo_heading" value="<?= $h($content['calc_promo']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Tekst</label><textarea name="calc_promo_text" rows="2"><?= $h($content['calc_promo']['text']) ?></textarea></div>
            <div class="field"><label>Tekst przycisku</label><input type="text" name="calc_promo_button_label" value="<?= $h($content['calc_promo']['button_label']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Dlaczego SecureWare"</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="why_eyebrow" value="<?= $h($content['why']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="why_heading" value="<?= $h($content['why']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="why_intro" rows="2"><?= $h($content['why']['intro']) ?></textarea></div>
            <div class="field"><label>Tekst linku</label><input type="text" name="why_link_label" value="<?= $h($content['why']['link_label']) ?>"></div>

            <?php foreach ($content['why']['items'] as $i => $item): ?>
                <div class="form-row">
                    <div class="field"><label>Pozycja <?= $i + 1 ?> — tytuł</label><input type="text" name="why_item_title[]" value="<?= $h($item['title']) ?>"></div>
                    <div class="field"><label>Pozycja <?= $i + 1 ?> — opis</label><input type="text" name="why_item_text[]" value="<?= $h($item['text']) ?>"></div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Case studies"</h2>
        <p class="hint" style="margin-top:-6px;">Prawdziwe, najlepiej zanonimizowane historie klientów z konkretnymi liczbami - to najmocniejszy dowód, więc nie zmyślaj tych danych.</p>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="cases_eyebrow" value="<?= $h($content['cases']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="cases_heading" value="<?= $h($content['cases']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="cases_intro" rows="2"><?= $h($content['cases']['intro']) ?></textarea></div>

            <div class="repeatable-rows" id="case-rows">
                <?php foreach ($content['cases']['items'] as $i => $item): ?>
                    <div class="row" style="flex-direction:column;align-items:stretch;gap:8px;border-top:1px solid var(--sw-border);padding-top:14px;margin-top:6px;">
                        <div class="form-row">
                            <div class="field"><label>Ikona</label><?php $iconSelect('case_item_icon[]', $item['icon']); ?></div>
                            <div class="field"><label>Branża</label><input type="text" name="case_item_industry[]" value="<?= $h($item['industry']) ?>" placeholder="np. E-commerce"></div>
                        </div>
                        <div class="field"><label>Nagłówek wyniku</label><input type="text" name="case_item_title[]" value="<?= $h($item['title']) ?>"></div>
                        <div class="field"><label>Sytuacja</label><textarea name="case_item_situation[]" rows="2"><?= $h($item['situation']) ?></textarea></div>
                        <div class="form-row">
                            <div class="field"><label>Metryka 1 — wartość</label><input type="text" name="case_item_metric1_value[]" value="<?= $h($item['metric1_value']) ?>" placeholder="np. 4h"></div>
                            <div class="field"><label>Metryka 1 — opis</label><input type="text" name="case_item_metric1_label[]" value="<?= $h($item['metric1_label']) ?>"></div>
                        </div>
                        <div class="form-row">
                            <div class="field"><label>Metryka 2 — wartość</label><input type="text" name="case_item_metric2_value[]" value="<?= $h($item['metric2_value']) ?>"></div>
                            <div class="field"><label>Metryka 2 — opis</label><input type="text" name="case_item_metric2_label[]" value="<?= $h($item['metric2_label']) ?>"></div>
                        </div>
                        <div class="form-row">
                            <div class="field"><label>Metryka 3 — wartość</label><input type="text" name="case_item_metric3_value[]" value="<?= $h($item['metric3_value']) ?>"></div>
                            <div class="field"><label>Metryka 3 — opis</label><input type="text" name="case_item_metric3_label[]" value="<?= $h($item['metric3_label']) ?>"></div>
                        </div>
                        <button type="button" class="button button--ghost button--small" data-remove-row style="align-self:flex-end;">Usuń case study</button>
                    </div>
                <?php endforeach; ?>
            </div>
            <button type="button" class="button button--ghost button--small" data-add-row="case-rows" style="align-self:flex-start;margin-top:6px;">+ Dodaj case study</button>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Wdrożenie krok po kroku"</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="steps_eyebrow" value="<?= $h($content['steps']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="steps_heading" value="<?= $h($content['steps']['heading']) ?>"></div>
            </div>
            <div class="field"><label>Wstęp</label><textarea name="steps_intro" rows="2"><?= $h($content['steps']['intro']) ?></textarea></div>

            <?php foreach ($content['steps']['items'] as $i => $item): ?>
                <div class="form-row">
                    <div class="field"><label>Krok <?= $i + 1 ?> — tytuł</label><input type="text" name="steps_item_title[]" value="<?= $h($item['title']) ?>"></div>
                    <div class="field"><label>Krok <?= $i + 1 ?> — opis</label><input type="text" name="steps_item_text[]" value="<?= $h($item['text']) ?>"></div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja "Z bloga"</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="blog_eyebrow" value="<?= $h($content['blog']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="blog_heading" value="<?= $h($content['blog']['heading']) ?>"></div>
            </div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">FAQ</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="faq_eyebrow" value="<?= $h($content['faq']['eyebrow']) ?>"></div>
                <div class="field"><label>Nagłówek</label><input type="text" name="faq_heading" value="<?= $h($content['faq']['heading']) ?>"></div>
            </div>
            <div class="field">
                <label>Pytania i odpowiedzi</label>
                <div class="repeatable-rows repeatable-rows--faq" id="faq-rows">
                    <?php foreach ($content['faq']['items'] as $item): ?>
                        <div class="row" style="flex-direction:column;align-items:stretch;gap:6px;">
                            <input type="text" name="faq_question[]" value="<?= $h($item['question']) ?>" placeholder="Pytanie">
                            <textarea name="faq_answer[]" rows="2" placeholder="Odpowiedź"><?= $h($item['answer']) ?></textarea>
                            <button type="button" class="button button--ghost button--small" data-remove-row style="align-self:flex-end;">Usuń</button>
                        </div>
                    <?php endforeach; ?>
                </div>
                <button type="button" class="button button--ghost button--small" data-add-row="faq-rows" style="align-self:flex-start;margin-top:6px;">+ Dodaj pytanie</button>
            </div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Sekcja końcowa (CTA)</h2>
        <div class="form-grid form-grid--wide">
            <div class="field"><label>Nagłówek</label><input type="text" name="cta_heading" value="<?= $h($content['cta']['heading']) ?>"></div>
            <div class="field"><label>Tekst</label><input type="text" name="cta_text" value="<?= $h($content['cta']['text']) ?>"></div>
            <div class="form-row">
                <div class="field"><label>Tekst przycisku</label><input type="text" name="cta_button_label" value="<?= $h($content['cta']['button_label']) ?>"></div>
                <div class="field"><label>Adres przycisku</label><input type="text" name="cta_button_url" value="<?= $h($content['cta']['button_url']) ?>"></div>
            </div>
        </div>
    </div>

    <div class="form-actions">
        <button type="submit" class="button">Zapisz treść strony głównej</button>
    </div>
</form>

<script src="/assets/js/admin.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/admin.js') ?: '1' ?>"></script>
<script>
(function () {
    var container = document.getElementById('faq-rows');
    var addBtn = document.querySelector('[data-add-row="faq-rows"]');
    if (!container || !addBtn) return;
    container.addEventListener('click', function (e) {
        if (e.target.matches('[data-remove-row]')) { e.preventDefault(); e.target.closest('.row').remove(); }
    });
    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var row = document.createElement('div');
        row.className = 'row';
        row.style.cssText = 'flex-direction:column;align-items:stretch;gap:6px;';
        row.innerHTML = '<input type="text" name="faq_question[]" placeholder="Pytanie">' +
            '<textarea name="faq_answer[]" rows="2" placeholder="Odpowiedź"></textarea>' +
            '<button type="button" class="button button--ghost button--small" data-remove-row style="align-self:flex-end;">Usuń</button>';
        container.appendChild(row);
    });
})();
(function () {
    var container = document.getElementById('case-rows');
    var addBtn = document.querySelector('[data-add-row="case-rows"]');
    if (!container || !addBtn) return;
    var iconOptions = <?= json_encode($icons) ?>.map(function (i) { return '<option value="' + i + '">' + i + '</option>'; }).join('');
    container.addEventListener('click', function (e) {
        if (e.target.matches('[data-remove-row]')) { e.preventDefault(); e.target.closest('.row').remove(); }
    });
    addBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var row = document.createElement('div');
        row.className = 'row';
        row.style.cssText = 'flex-direction:column;align-items:stretch;gap:8px;border-top:1px solid var(--sw-border);padding-top:14px;margin-top:6px;';
        row.innerHTML =
            '<div class="form-row">' +
                '<div class="field"><label>Ikona</label><select name="case_item_icon[]">' + iconOptions + '</select></div>' +
                '<div class="field"><label>Branża</label><input type="text" name="case_item_industry[]" placeholder="np. E-commerce"></div>' +
            '</div>' +
            '<div class="field"><label>Nagłówek wyniku</label><input type="text" name="case_item_title[]"></div>' +
            '<div class="field"><label>Sytuacja</label><textarea name="case_item_situation[]" rows="2"></textarea></div>' +
            '<div class="form-row">' +
                '<div class="field"><label>Metryka 1 — wartość</label><input type="text" name="case_item_metric1_value[]" placeholder="np. 4h"></div>' +
                '<div class="field"><label>Metryka 1 — opis</label><input type="text" name="case_item_metric1_label[]"></div>' +
            '</div>' +
            '<div class="form-row">' +
                '<div class="field"><label>Metryka 2 — wartość</label><input type="text" name="case_item_metric2_value[]"></div>' +
                '<div class="field"><label>Metryka 2 — opis</label><input type="text" name="case_item_metric2_label[]"></div>' +
            '</div>' +
            '<div class="form-row">' +
                '<div class="field"><label>Metryka 3 — wartość</label><input type="text" name="case_item_metric3_value[]"></div>' +
                '<div class="field"><label>Metryka 3 — opis</label><input type="text" name="case_item_metric3_label[]"></div>' +
            '</div>' +
            '<button type="button" class="button button--ghost button--small" data-remove-row style="align-self:flex-end;">Usuń case study</button>';
        container.appendChild(row);
    });
})();
</script>
