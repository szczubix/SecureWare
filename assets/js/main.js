/**
 * SecureWare - Main JavaScript
 *
 * @package SecureWare
 */

(function () {
    'use strict';

    /**
     * Sticky header - add bg on scroll
     */
    function initStickyHeader() {
        var header = document.getElementById('sw-header');
        if (!header) return;

        function updateHeader() {
            if (window.scrollY > 30) {
                header.classList.add('is-scrolled');
            } else {
                header.classList.remove('is-scrolled');
            }
        }

        updateHeader();
        window.addEventListener('scroll', updateHeader, { passive: true });
    }

    /**
     * Mobile burger menu
     */
    function initBurgerMenu() {
        var burger = document.getElementById('sw-burger');
        var nav = document.getElementById('sw-nav');
        if (!burger || !nav) return;

        burger.addEventListener('click', function () {
            burger.classList.toggle('is-active');
            nav.classList.toggle('is-open');
        });

        document.addEventListener('click', function (e) {
            if (nav.classList.contains('is-open') && !e.target.closest('#sw-nav') && !e.target.closest('#sw-burger')) {
                nav.classList.remove('is-open');
                burger.classList.remove('is-active');
            }
        });
    }

    /**
     * Search toggle (dropdown)
     */
    function initSearchToggle() {
        var toggle = document.getElementById('sw-search-toggle');
        var form = document.getElementById('sw-search-form');
        if (!toggle || !form) return;

        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            form.classList.toggle('is-open');
            if (form.classList.contains('is-open')) {
                var input = form.querySelector('input[type="search"]');
                if (input) input.focus();
            }
        });

        document.addEventListener('click', function (e) {
            if (form.classList.contains('is-open') && !e.target.closest('#sw-search')) {
                form.classList.remove('is-open');
            }
        });
    }

    /**
     * Copy license key to clipboard
     */
    function initCopyButtons() {
        document.addEventListener('click', function (e) {
            var button = e.target.closest('.sw-license-key__copy');
            if (!button) return;

            var key = button.getAttribute('data-key');
            if (!key) return;

            navigator.clipboard.writeText(key).then(function () {
                var originalText = button.textContent;
                button.textContent = typeof securewareData !== 'undefined' && securewareData.strings
                    ? securewareData.strings.copied
                    : 'Skopiowano!';
                button.style.borderColor = 'var(--sw-success)';
                button.style.color = 'var(--sw-success)';

                setTimeout(function () {
                    button.textContent = originalText;
                    button.style.borderColor = '';
                    button.style.color = '';
                }, 2000);
            });
        });
    }

    /**
     * Smooth scroll for anchor links
     */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
            anchor.addEventListener('click', function (e) {
                var targetId = this.getAttribute('href');
                if (targetId === '#') return;

                var target = document.querySelector(targetId);
                if (!target) return;

                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                });
            });
        });
    }

    /**
     * Initialize
     */
    document.addEventListener('DOMContentLoaded', function () {
        initStickyHeader();
        initBurgerMenu();
        initSearchToggle();
        initCopyButtons();
        initSmoothScroll();
    });
})();
