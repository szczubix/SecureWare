/**
 * SecureWare - Main JavaScript
 *
 * @package SecureWare
 */

(function () {
    'use strict';

    /**
     * Mobile menu toggle
     */
    function initMobileMenu() {
        var toggle = document.getElementById('sw-menu-toggle');
        if (!toggle) return;

        toggle.addEventListener('click', function () {
            var catnav = document.getElementById('sw-catnav');
            if (catnav) {
                catnav.classList.toggle('is-open');
                toggle.classList.toggle('is-active');
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            var catnav = document.getElementById('sw-catnav');
            if (catnav && catnav.classList.contains('is-open') && !e.target.closest('#sw-catnav') && !e.target.closest('#sw-menu-toggle')) {
                catnav.classList.remove('is-open');
                toggle.classList.remove('is-active');
            }
        });
    }

    /**
     * Sticky header - hide topbar on scroll
     */
    function initStickyHeader() {
        var header = document.getElementById('sw-header');
        if (!header) return;

        var lastScroll = 0;

        window.addEventListener('scroll', function () {
            var currentScroll = window.scrollY;

            if (currentScroll > 50) {
                header.classList.add('is-scrolled');
            } else {
                header.classList.remove('is-scrolled');
            }

            lastScroll = currentScroll;
        }, { passive: true });
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
                button.textContent = securewareData && securewareData.strings
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
     * Search form focus state
     */
    function initSearchToggle() {
        var searchForm = document.querySelector('.sw-header__search');
        if (!searchForm) return;

        var input = searchForm.querySelector('input');
        if (input) {
            input.addEventListener('focus', function () {
                searchForm.classList.add('is-active');
            });
            input.addEventListener('blur', function () {
                searchForm.classList.remove('is-active');
            });
        }
    }

    /**
     * Initialize all components when DOM is ready
     */
    document.addEventListener('DOMContentLoaded', function () {
        initMobileMenu();
        initStickyHeader();
        initCopyButtons();
        initSmoothScroll();
        initSearchToggle();
    });
})();
