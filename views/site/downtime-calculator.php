<?php
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <div class="meta sw-anim-in" style="color:#8791a8;font-size:13.5px;font-weight:600;margin-bottom:14px;"><a href="<?= Locale::url('/') ?>" style="color:#aab4c8;">&larr; <?= Lang::t('breadcrumb.home') ?></a></div>
        <span class="sw-hero__eyebrow sw-anim-in sw-delay-1"><?= Lang::t('calc.eyebrow') ?></span>
        <h1 class="sw-anim-in sw-delay-2" style="font-size:36px;"><?= Lang::t('calc.heading') ?></h1>
        <p class="lead sw-anim-in sw-delay-3"><?= Lang::t('calc.lead') ?></p>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap sw-calc">
        <div class="sw-form reveal sw-calc__form">
            <label><?= Lang::t('calc.label_employees') ?>
                <input type="number" id="calc-employees" min="0" value="10">
            </label>
            <label><?= Lang::t('calc.label_wage') ?>
                <input type="number" id="calc-wage" min="0" value="60">
            </label>
            <label><?= Lang::t('calc.label_revenue') ?>
                <input type="number" id="calc-revenue" min="0" value="0">
                <span class="sw-calc__hint"><?= Lang::t('calc.hint_revenue') ?></span>
            </label>
            <label><?= Lang::t('calc.label_hours') ?> <strong id="calc-hours-out">8h</strong>
                <input type="range" id="calc-hours" min="1" max="72" value="8">
            </label>
        </div>

        <div class="sw-calc__result reveal">
            <p class="sw-calc__result-label"><?= Lang::t('calc.result_label') ?></p>
            <div class="sw-calc__total" id="calc-total">0 zł</div>
            <div class="sw-calc__breakdown">
                <div>
                    <span><?= Lang::t('calc.breakdown_productivity') ?></span>
                    <strong id="calc-productivity">0 zł</strong>
                </div>
                <div id="calc-revenue-row" style="display:none;">
                    <span><?= Lang::t('calc.breakdown_revenue') ?></span>
                    <strong id="calc-revenue-cost">0 zł</strong>
                </div>
            </div>
            <p class="sw-calc__disclaimer"><?= Lang::t('calc.disclaimer') ?></p>
            <a href="<?= Locale::url('/kontakt') ?>" class="sw-btn sw-btn--primary" style="width:100%;justify-content:center;"><?= Lang::t('calc.cta') ?></a>
        </div>
    </div>
</section>

<script>
(function () {
    var employeesEl = document.getElementById('calc-employees');
    var wageEl = document.getElementById('calc-wage');
    var revenueEl = document.getElementById('calc-revenue');
    var hoursEl = document.getElementById('calc-hours');
    var hoursOut = document.getElementById('calc-hours-out');
    var totalEl = document.getElementById('calc-total');
    var productivityEl = document.getElementById('calc-productivity');
    var revenueCostEl = document.getElementById('calc-revenue-cost');
    var revenueRow = document.getElementById('calc-revenue-row');

    function fmt(n) {
        return Math.round(n).toLocaleString('pl-PL') + ' zł';
    }

    function recalc() {
        var employees = Math.max(0, parseFloat(employeesEl.value) || 0);
        var wage = Math.max(0, parseFloat(wageEl.value) || 0);
        var revenue = Math.max(0, parseFloat(revenueEl.value) || 0);
        var hours = Math.max(1, parseFloat(hoursEl.value) || 1);

        hoursOut.textContent = hours + 'h';

        var productivityCost = employees * wage * hours;
        var revenueCost = revenue > 0 ? (revenue / (250 * 8)) * hours : 0;
        var total = productivityCost + revenueCost;

        productivityEl.textContent = fmt(productivityCost);
        if (revenue > 0) {
            revenueRow.style.display = '';
            revenueCostEl.textContent = fmt(revenueCost);
        } else {
            revenueRow.style.display = 'none';
        }
        totalEl.textContent = fmt(total);
    }

    [employeesEl, wageEl, revenueEl, hoursEl].forEach(function (el) {
        el.addEventListener('input', recalc);
    });
    recalc();
})();
</script>
