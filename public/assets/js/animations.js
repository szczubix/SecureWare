/**
 * Lekki system animacji strony publicznej - scroll reveal (IntersectionObserver)
 * + cien nagłówka przy przewijaniu. Bez zewnetrznych zaleznosci. Nic nie robi,
 * gdy uzytkownik ustawil "ogranicz animacje" w systemie (prefers-reduced-motion) -
 * elementy zostaja od razu w pelni widoczne (patrz CSS).
 */
(function () {
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reduceMotion || !('IntersectionObserver' in window)) {
        document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
            el.classList.add('is-visible');
        });
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
                observer.unobserve(el);
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

        document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
            observer.observe(el);
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
})();
