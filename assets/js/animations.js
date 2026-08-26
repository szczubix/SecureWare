/**
 * Lekki system animacji strony publicznej - scroll reveal (IntersectionObserver)
 * + cien nagłówka przy przewijaniu. Bez zewnetrznych zaleznosci. Nic nie robi,
 * gdy uzytkownik ustawil "ogranicz animacje" w systemie (prefers-reduced-motion) -
 * elementy zostaja od razu w pelni widoczne (patrz CSS).
 */
(function () {
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Count-up animation - shared by any [data-count] element, triggered
    // when it actually scrolls into view (not on page load), so numbers
    // further down the page (e.g. the stats band) animate when seen.
    function startCountUp(el) {
        var target = parseInt(el.getAttribute('data-count'), 10);
        var suffix = el.getAttribute('data-suffix') || '';
        if (reduceMotion || isNaN(target)) {
            el.textContent = target + suffix;
            return;
        }
        var start = null;
        var duration = 1400;
        function step(ts) {
            if (!start) start = ts;
            var progress = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target) + suffix;
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    if (reduceMotion || !('IntersectionObserver' in window)) {
        document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
            el.classList.add('is-visible');
        });
        document.querySelectorAll('[data-count]').forEach(startCountUp);
    } else {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                var el = entry.target;

                if (el.classList.contains('reveal-stagger')) {
                    Array.prototype.forEach.call(el.children, function (child, i) {
                        child.style.transitionDelay = (i * 80) + 'ms';
                    });
                }

                el.classList.add('is-visible');
                el.querySelectorAll('[data-count]').forEach(function (el2) {
                    setTimeout(function () { startCountUp(el2); }, 300);
                });
                observer.unobserve(el);
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

        document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
            observer.observe(el);
        });

        // [data-count] elements outside any .reveal/.reveal-stagger container
        // (e.g. above-the-fold hero content) aren't scroll-gated - count up
        // right away like the rest of the hero's entrance animation.
        document.querySelectorAll('[data-count]').forEach(function (el) {
            if (!el.closest('.reveal, .reveal-stagger')) {
                setTimeout(function () { startCountUp(el); }, 500);
            }
        });
    }

    var header = document.querySelector('.sw-header');
    if (header) {
        var onScroll = function () {
            header.classList.toggle('is-scrolled', window.scrollY > 12);
        };
        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    // 3-2-1-1-0 rule flow diagram: each node expands its own detail panel independently.
    document.querySelectorAll('.sw-rule__node').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var expanded = btn.getAttribute('aria-expanded') === 'true';
            btn.setAttribute('aria-expanded', String(!expanded));
            var panel = btn.parentElement.querySelector('.sw-rule__panel');
            if (panel) panel.classList.toggle('is-open', !expanded);
        });
    });

    // Platform tabs on the homepage ("Backup" / "Disaster Recovery" / "Monitoring").
    document.querySelectorAll('.sw-platform').forEach(function (wrap) {
        var tabs = wrap.querySelectorAll('.sw-platform__tab');
        var panels = wrap.querySelectorAll('.sw-platform__panel');
        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () {
                tabs.forEach(function (t) { t.classList.remove('is-active'); t.setAttribute('aria-selected', 'false'); });
                panels.forEach(function (p) { p.classList.remove('is-active'); });
                tab.classList.add('is-active');
                tab.setAttribute('aria-selected', 'true');
                var target = wrap.querySelector('.sw-platform__panel[data-panel="' + tab.getAttribute('data-tab') + '"]');
                if (target) {
                    target.classList.add('is-active');
                    target.querySelectorAll('li').forEach(function (li, i) {
                        li.style.transition = 'none';
                        li.style.opacity = '0';
                        li.style.transform = 'translateY(8px)';
                        void li.offsetWidth;
                        li.style.transition = 'opacity .4s ease ' + (i * 90) + 'ms, transform .4s ease ' + (i * 90) + 'ms';
                        li.style.opacity = '1';
                        li.style.transform = 'translateY(0)';
                    });
                }
            });
        });
    });
})();
