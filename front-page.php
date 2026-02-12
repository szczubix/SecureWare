<?php
/**
 * SecureWare - Front Page Template
 *
 * @package SecureWare
 */

get_header();
?>

<!-- HERO BANNER -->
<section class="sw-hero">
    <div class="sw-hero__bg"></div>
    <div class="sw-container">
        <div class="sw-hero__content">
            <h1 class="sw-hero__title">
                <?php echo wp_kses_post( get_theme_mod( 'secureware_hero_title', __( 'LICENCJE, KTÓRE<br><span>PO PROSTU DZIAŁAJĄ</span>', 'secureware' ) ) ); ?>
            </h1>
            <p class="sw-hero__text">
                <?php echo esc_html( get_theme_mod( 'secureware_hero_description', __( 'Oryginalne klucze aktywacyjne — kupujesz, dostajesz na maila i od razu korzystasz. Bez czekania, bez komplikacji.', 'secureware' ) ) ); ?>
            </p>
            <?php if ( class_exists( 'WooCommerce' ) ) : ?>
            <a class="sw-hero__btn" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                <?php esc_html_e( 'PRZEJDŹ DO SKLEPU', 'secureware' ); ?>
            </a>
            <?php endif; ?>
        </div>
    </div>
</section>

<?php if ( class_exists( 'WooCommerce' ) ) : ?>

<!-- WHY BUY FROM US -->
<section class="sw-why">
    <div class="sw-container">
        <header class="sw-section-head">
            <h5><?php esc_html_e( 'Dlaczego my', 'secureware' ); ?></h5>
            <h3><?php esc_html_e( '4 POWODY', 'secureware' ); ?></h3>
        </header>
        <div class="sw-why__grid">
            <div class="sw-why__item">
                <div class="sw-why__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                <h6><?php esc_html_e( 'BŁYSKAWICZNA DOSTAWA', 'secureware' ); ?></h6>
                <p><?php esc_html_e( 'Kupujesz — klucz ląduje na Twoim mailu. Dosłownie w kilka sekund.', 'secureware' ); ?></p>
            </div>
            <div class="sw-why__item">
                <div class="sw-why__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <h6><?php esc_html_e( '100% ORYGINALNE', 'secureware' ); ?></h6>
                <p><?php esc_html_e( 'Żadnych podróbek. Tylko oficjalne licencje od autoryzowanych dystrybutorów.', 'secureware' ); ?></p>
            </div>
            <div class="sw-why__item">
                <div class="sw-why__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                <h6><?php esc_html_e( 'GWARANCJA DZIAŁANIA', 'secureware' ); ?></h6>
                <p><?php esc_html_e( 'Każdy klucz testujemy. Jeśli coś nie zadziała — wymienimy lub zwrócimy pieniądze.', 'secureware' ); ?></p>
            </div>
            <div class="sw-why__item">
                <div class="sw-why__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                </div>
                <h6><?php esc_html_e( 'WSPARCIE TECHNICZNE', 'secureware' ); ?></h6>
                <p><?php esc_html_e( 'Nie wiesz jak zainstalować? Piszesz lub dzwonisz — pomagamy od ręki.', 'secureware' ); ?></p>
            </div>
        </div>
    </div>
</section>

<!-- SUPPORT / GUARANTEE -->
<section class="sw-divided">
    <div class="sw-container">
        <div class="sw-divided__inner">
            <div class="sw-divided__left">
                <h4><?php esc_html_e( 'NIE ZOSTAWIAMY CIĘ', 'secureware' ); ?></h4>
                <h4><?php esc_html_e( 'Z KLUCZEM I PYTANIAMI.', 'secureware' ); ?></h4>
            </div>
            <div class="sw-divided__right">
                <header class="sw-section-head sw-section-head--left">
                    <h5><?php esc_html_e( 'Profesjonalne', 'secureware' ); ?></h5>
                    <h3><?php esc_html_e( 'WSPARCIE', 'secureware' ); ?></h3>
                </header>
                <p><?php esc_html_e( 'Kupno to dopiero początek — pomożemy Ci wszystko uruchomić, skonfigurować i ogarnąć. Zero stresu, zero dodatkowych kosztów.', 'secureware' ); ?></p>
                <p><?php esc_html_e( 'Piszesz maila albo dzwonisz i temat załatwiony. Tak to u nas wygląda.', 'secureware' ); ?></p>
            </div>
        </div>
    </div>
</section>

<!-- OFFER / CATEGORIES -->
<section class="sw-offer">
    <div class="sw-container">
        <header class="sw-section-head">
            <h5><?php esc_html_e( 'Co u nas znajdziesz', 'secureware' ); ?></h5>
            <h3><?php esc_html_e( 'KATEGORIE', 'secureware' ); ?></h3>
        </header>
        <a class="sw-cta-btn" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">
            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <?php esc_html_e( 'PRZEJDŹ DO SKLEPU', 'secureware' ); ?>
        </a>
        <div class="sw-offer__grid">
            <?php
            $categories = get_terms( array(
                'taxonomy'   => 'product_cat',
                'hide_empty' => true,
                'number'     => 6,
                'exclude'    => array( get_option( 'default_product_cat' ) ),
            ) );

            $cat_icons = array(
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
            );

            $fallback_names = array(
                __( 'Systemy operacyjne', 'secureware' ),
                __( 'Antywirus i bezpieczeństwo', 'secureware' ),
                __( 'Pakiety biurowe', 'secureware' ),
                __( 'Narzędzia deweloperskie', 'secureware' ),
                __( 'Narzędzia systemowe', 'secureware' ),
                __( 'Subskrypcje', 'secureware' ),
            );

            if ( ! empty( $categories ) && ! is_wp_error( $categories ) ) :
                $i = 0;
                foreach ( $categories as $category ) :
                    $icon = $cat_icons[ $i % count( $cat_icons ) ];
                    $link = get_term_link( $category );
            ?>
                <a href="<?php echo esc_url( $link ); ?>" class="sw-offer__item">
                    <div class="sw-offer__icon"><?php echo $icon; // phpcs:ignore ?></div>
                    <span class="sw-offer__name"><?php echo esc_html( $category->name ); ?></span>
                    <div class="sw-offer__link">
                        <span>
                            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            <?php esc_html_e( 'ZOBACZ PRODUKTY', 'secureware' ); ?>
                        </span>
                    </div>
                </a>
            <?php
                    $i++;
                endforeach;
            else :
                for ( $i = 0; $i < 6; $i++ ) :
            ?>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-offer__item">
                    <div class="sw-offer__icon"><?php echo $cat_icons[ $i ]; // phpcs:ignore ?></div>
                    <span class="sw-offer__name"><?php echo esc_html( $fallback_names[ $i ] ); ?></span>
                    <div class="sw-offer__link">
                        <span>
                            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            <?php esc_html_e( 'ZOBACZ PRODUKTY', 'secureware' ); ?>
                        </span>
                    </div>
                </a>
            <?php
                endfor;
            endif;
            ?>
        </div>
    </div>
</section>

<!-- FEATURED PRODUCTS -->
<section class="sw-products-section">
    <div class="sw-container">
        <header class="sw-section-head">
            <h5><?php esc_html_e( 'Sprawdź co mamy', 'secureware' ); ?></h5>
            <h3><?php esc_html_e( 'BESTSELLERY', 'secureware' ); ?></h3>
        </header>
        <?php echo do_shortcode( '[products limit="8" columns="4" orderby="popularity" visibility="featured"]' ); ?>
    </div>
</section>

<!-- CONTACT / ADVISE -->
<section class="sw-divided sw-divided--accent">
    <div class="sw-container">
        <div class="sw-divided__inner">
            <div class="sw-divided__left sw-divided__left--cta">
                <h5><?php esc_html_e( 'ZADZWOŃ DO NAS', 'secureware' ); ?></h5>
                <?php
                $phone = get_theme_mod( 'secureware_company_phone', '' );
                if ( $phone ) :
                ?>
                <a href="tel:<?php echo esc_attr( preg_replace( '/[^+0-9]/', '', $phone ) ); ?>" class="sw-divided__phone"><?php echo esc_html( $phone ); ?></a>
                <?php endif; ?>
                <h5><?php esc_html_e( 'LUB NAPISZ', 'secureware' ); ?></h5>
                <?php
                $email = get_theme_mod( 'secureware_company_email', '' );
                if ( $email ) :
                ?>
                <a href="mailto:<?php echo esc_attr( $email ); ?>" class="sw-cta-btn sw-cta-btn--light">
                    <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    <?php esc_html_e( 'NAPISZ DO NAS', 'secureware' ); ?>
                </a>
                <?php endif; ?>
            </div>
            <div class="sw-divided__right">
                <header class="sw-section-head sw-section-head--left sw-section-head--light">
                    <h5><?php esc_html_e( 'Nie wiesz co wybrać?', 'secureware' ); ?></h5>
                    <h3><?php esc_html_e( 'DORADZIMY', 'secureware' ); ?></h3>
                </header>
                <div class="sw-divided__list">
                    <div class="sw-divided__list-item">
                        <span class="sw-divided__list-num">1</span>
                        <span><?php esc_html_e( 'Dobierzemy licencję do Twoich potrzeb — do firmy, do domu, na jedno lub wiele stanowisk.', 'secureware' ); ?></span>
                    </div>
                    <div class="sw-divided__list-item">
                        <span class="sw-divided__list-num">2</span>
                        <span><?php esc_html_e( 'Przeprowadzimy Cię przez instalację i aktywację krok po kroku.', 'secureware' ); ?></span>
                    </div>
                    <div class="sw-divided__list-item">
                        <span class="sw-divided__list-num">3</span>
                        <span><?php esc_html_e( 'Podpowiemy jak zabezpieczyć dane i dobrać optymalny pakiet ochrony.', 'secureware' ); ?></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- PROMOTIONS -->
<section class="sw-products-section">
    <div class="sw-container">
        <header class="sw-section-head">
            <h5><?php esc_html_e( 'Złap okazję', 'secureware' ); ?></h5>
            <h3><?php esc_html_e( 'PROMOCJE', 'secureware' ); ?></h3>
        </header>
        <?php echo do_shortcode( '[products limit="4" columns="4" on_sale="true" orderby="date"]' ); ?>
    </div>
</section>

<!-- NEWSLETTER -->
<section class="sw-divided sw-divided--dark">
    <div class="sw-container">
        <div class="sw-divided__inner">
            <div class="sw-divided__left">
                <header class="sw-section-head sw-section-head--left">
                    <h5><?php echo esc_html( get_theme_mod( 'secureware_cta_title', __( 'Bądź na bieżąco', 'secureware' ) ) ); ?></h5>
                    <h3><?php esc_html_e( 'NEWSLETTER', 'secureware' ); ?></h3>
                </header>
                <p><?php echo esc_html( get_theme_mod( 'secureware_cta_description', __( 'Nowe produkty, kody rabatowe i promocje — prosto na Twój e-mail. Żadnego spamu, obiecujemy.', 'secureware' ) ) ); ?></p>
            </div>
            <div class="sw-divided__right sw-divided__right--newsletter">
                <form class="sw-newsletter-form" action="#" method="post">
                    <input type="email" name="email" placeholder="<?php esc_attr_e( 'WPISZ ADRES E-MAIL', 'secureware' ); ?>" required>
                    <button type="submit"><?php esc_html_e( 'Zapisz się', 'secureware' ); ?></button>
                </form>
                <ul class="sw-newsletter-info">
                    <li><?php esc_html_e( 'Dbamy o Twoją prywatność.', 'secureware' ); ?></li>
                    <li><?php esc_html_e( 'Nie wysyłamy spamu.', 'secureware' ); ?></li>
                    <li><?php esc_html_e( 'W każdej chwili możesz się wypisać.', 'secureware' ); ?></li>
                </ul>
            </div>
        </div>
    </div>
</section>

<?php endif; ?>

<?php get_footer(); ?>
