<?php
/**
 * SecureWare - Front Page Template
 *
 * @package SecureWare
 */

get_header();
?>

<?php if ( class_exists( 'WooCommerce' ) ) : ?>

<!-- Promo banner -->
<section class="sw-promo">
    <div class="sw-container">
        <div class="sw-promo__banner">
            <div class="sw-promo__content">
                <span class="sw-promo__tag"><?php esc_html_e( 'Autoryzowany sklep', 'secureware' ); ?></span>
                <h1 class="sw-promo__title">
                    <?php echo wp_kses_post( get_theme_mod( 'secureware_hero_title', __( 'Oryginalne licencje na oprogramowanie', 'secureware' ) ) ); ?>
                </h1>
                <p class="sw-promo__desc">
                    <?php echo esc_html( get_theme_mod( 'secureware_hero_description', __( 'Klucze aktywacyjne z natychmiastową dostawą na e-mail. Najlepsze ceny, wsparcie techniczne.', 'secureware' ) ) ); ?>
                </p>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-btn sw-btn--primary sw-btn--lg">
                    <?php esc_html_e( 'Przejdź do sklepu', 'secureware' ); ?>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                </a>
            </div>
            <div class="sw-promo__stats">
                <div class="sw-promo__stat">
                    <span class="sw-promo__stat-val"><?php echo esc_html( get_theme_mod( 'secureware_stat_products', '500+' ) ); ?></span>
                    <span class="sw-promo__stat-lbl"><?php esc_html_e( 'produktów', 'secureware' ); ?></span>
                </div>
                <div class="sw-promo__stat">
                    <span class="sw-promo__stat-val"><?php echo esc_html( get_theme_mod( 'secureware_stat_clients', '10k+' ) ); ?></span>
                    <span class="sw-promo__stat-lbl"><?php esc_html_e( 'klientów', 'secureware' ); ?></span>
                </div>
                <div class="sw-promo__stat">
                    <span class="sw-promo__stat-val">&lt; 1 min</span>
                    <span class="sw-promo__stat-lbl"><?php esc_html_e( 'czas dostawy', 'secureware' ); ?></span>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Categories grid -->
<section class="sw-section">
    <div class="sw-container">
        <div class="sw-section-header">
            <h2><?php esc_html_e( 'Kategorie produktów', 'secureware' ); ?></h2>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-section-header__link">
                <?php esc_html_e( 'Wszystkie kategorie', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <div class="sw-cat-grid">
            <?php
            $categories = get_terms( array(
                'taxonomy'   => 'product_cat',
                'hide_empty' => true,
                'number'     => 6,
                'exclude'    => array( get_option( 'default_product_cat' ) ),
            ) );

            $category_icons = array(
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.26.604.852.997 1.51 1H21a2 2 0 0 1 0 4h-.09c-.66.003-1.25.396-1.51 1z"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
            );

            if ( ! empty( $categories ) && ! is_wp_error( $categories ) ) :
                $i = 0;
                foreach ( $categories as $category ) :
                    $icon = $category_icons[ $i % count( $category_icons ) ];
                    $link = get_term_link( $category );
            ?>
                <a href="<?php echo esc_url( $link ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon">
                        <?php echo $icon; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </div>
                    <span class="sw-cat-tile__name"><?php echo esc_html( $category->name ); ?></span>
                    <span class="sw-cat-tile__count">
                        <?php
                        echo esc_html( sprintf(
                            _n( '%d produkt', '%d produktów', $category->count, 'secureware' ),
                            $category->count
                        ) );
                        ?>
                    </span>
                </a>
            <?php
                    $i++;
                endforeach;
            else :
            ?>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon"><?php echo $category_icons[0]; // phpcs:ignore ?></div>
                    <span class="sw-cat-tile__name"><?php esc_html_e( 'Systemy operacyjne', 'secureware' ); ?></span>
                    <span class="sw-cat-tile__count"><?php esc_html_e( 'Windows, macOS', 'secureware' ); ?></span>
                </a>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon"><?php echo $category_icons[1]; // phpcs:ignore ?></div>
                    <span class="sw-cat-tile__name"><?php esc_html_e( 'Antywirus', 'secureware' ); ?></span>
                    <span class="sw-cat-tile__count"><?php esc_html_e( 'Norton, Kaspersky, ESET', 'secureware' ); ?></span>
                </a>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon"><?php echo $category_icons[2]; // phpcs:ignore ?></div>
                    <span class="sw-cat-tile__name"><?php esc_html_e( 'Pakiety biurowe', 'secureware' ); ?></span>
                    <span class="sw-cat-tile__count"><?php esc_html_e( 'Microsoft Office, Adobe', 'secureware' ); ?></span>
                </a>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon"><?php echo $category_icons[3]; // phpcs:ignore ?></div>
                    <span class="sw-cat-tile__name"><?php esc_html_e( 'Narzędzia deweloperskie', 'secureware' ); ?></span>
                    <span class="sw-cat-tile__count"><?php esc_html_e( 'IDE, serwery, bazy danych', 'secureware' ); ?></span>
                </a>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon"><?php echo $category_icons[4]; // phpcs:ignore ?></div>
                    <span class="sw-cat-tile__name"><?php esc_html_e( 'Narzędzia systemowe', 'secureware' ); ?></span>
                    <span class="sw-cat-tile__count"><?php esc_html_e( 'Backup, optymalizacja', 'secureware' ); ?></span>
                </a>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-cat-tile">
                    <div class="sw-cat-tile__icon"><?php echo $category_icons[5]; // phpcs:ignore ?></div>
                    <span class="sw-cat-tile__name"><?php esc_html_e( 'Subskrypcje', 'secureware' ); ?></span>
                    <span class="sw-cat-tile__count"><?php esc_html_e( 'Microsoft 365, Adobe CC', 'secureware' ); ?></span>
                </a>
            <?php endif; ?>
        </div>
    </div>
</section>

<!-- Bestsellers -->
<section class="sw-section sw-section--products">
    <div class="sw-container">
        <div class="sw-section-header">
            <h2><?php esc_html_e( 'Bestsellery', 'secureware' ); ?></h2>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>?orderby=popularity" class="sw-section-header__link">
                <?php esc_html_e( 'Zobacz wszystkie', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <?php echo do_shortcode( '[products limit="8" columns="4" orderby="popularity" visibility="featured"]' ); ?>
    </div>
</section>

<!-- Promotions -->
<section class="sw-section sw-section--alt sw-section--products">
    <div class="sw-container">
        <div class="sw-section-header">
            <div class="sw-section-header__left">
                <h2><?php esc_html_e( 'Promocje', 'secureware' ); ?></h2>
                <span class="sw-section-header__badge"><?php esc_html_e( 'Oszczędź do -50%', 'secureware' ); ?></span>
            </div>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>?on_sale=1" class="sw-section-header__link">
                <?php esc_html_e( 'Wszystkie promocje', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <?php echo do_shortcode( '[products limit="4" columns="4" on_sale="true" orderby="date"]' ); ?>
    </div>
</section>

<!-- Features strip -->
<section class="sw-features-strip">
    <div class="sw-container">
        <div class="sw-features-strip__grid">
            <div class="sw-features-strip__item">
                <div class="sw-features-strip__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                <div>
                    <strong><?php esc_html_e( 'Błyskawiczna dostawa', 'secureware' ); ?></strong>
                    <span><?php esc_html_e( 'Klucz na e-mail w kilka sekund', 'secureware' ); ?></span>
                </div>
            </div>
            <div class="sw-features-strip__item">
                <div class="sw-features-strip__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <div>
                    <strong><?php esc_html_e( '100% oryginalne', 'secureware' ); ?></strong>
                    <span><?php esc_html_e( 'Autoryzowany dystrybutor', 'secureware' ); ?></span>
                </div>
            </div>
            <div class="sw-features-strip__item">
                <div class="sw-features-strip__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                </div>
                <div>
                    <strong><?php esc_html_e( 'Wsparcie techniczne', 'secureware' ); ?></strong>
                    <span><?php esc_html_e( 'Pomoc z instalacją i aktywacją', 'secureware' ); ?></span>
                </div>
            </div>
            <div class="sw-features-strip__item">
                <div class="sw-features-strip__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                </div>
                <div>
                    <strong><?php esc_html_e( 'Bezpieczne płatności', 'secureware' ); ?></strong>
                    <span><?php esc_html_e( 'BLIK, karty, przelewy', 'secureware' ); ?></span>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Latest products -->
<section class="sw-section sw-section--products">
    <div class="sw-container">
        <div class="sw-section-header">
            <h2><?php esc_html_e( 'Nowości w ofercie', 'secureware' ); ?></h2>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>?orderby=date" class="sw-section-header__link">
                <?php esc_html_e( 'Więcej nowości', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <?php echo do_shortcode( '[products limit="4" columns="4" orderby="date"]' ); ?>
    </div>
</section>

<?php endif; ?>

<!-- Newsletter -->
<section class="sw-section sw-section--alt">
    <div class="sw-container">
        <div class="sw-newsletter">
            <div class="sw-newsletter__text">
                <h2><?php echo esc_html( get_theme_mod( 'secureware_cta_title', __( 'Bądź na bieżąco', 'secureware' ) ) ); ?></h2>
                <p><?php echo esc_html( get_theme_mod( 'secureware_cta_description', __( 'Zapisz się do newslettera i otrzymuj informacje o promocjach i nowościach.', 'secureware' ) ) ); ?></p>
            </div>
            <form class="sw-newsletter__form" action="#" method="post">
                <input type="email" name="email" placeholder="<?php esc_attr_e( 'Twój adres e-mail', 'secureware' ); ?>" required>
                <button type="submit" class="sw-btn sw-btn--primary"><?php esc_html_e( 'Zapisz się', 'secureware' ); ?></button>
            </form>
        </div>
    </div>
</section>

<?php get_footer(); ?>
