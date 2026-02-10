<?php
/**
 * SecureWare - Front Page Template
 *
 * @package SecureWare
 */

get_header();
?>

<section class="sw-hero">
    <div class="sw-container">
        <div class="sw-hero__content">
            <div class="sw-hero__badge">
                <?php esc_html_e( 'Autoryzowany sprzedawca licencji', 'secureware' ); ?>
            </div>
            <h1 class="sw-hero__title">
                <?php echo wp_kses_post( get_theme_mod( 'secureware_hero_title', __( 'Oryginalne licencje na <span>oprogramowanie</span>', 'secureware' ) ) ); ?>
            </h1>
            <p class="sw-hero__description">
                <?php echo esc_html( get_theme_mod( 'secureware_hero_description', __( 'Kup licencje na najlepsze oprogramowanie w najniższych cenach. Natychmiastowa dostawa kluczy na e-mail.', 'secureware' ) ) ); ?>
            </p>
            <div class="sw-hero__buttons">
                <a href="<?php echo esc_url( class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'shop' ) : '#' ); ?>" class="sw-btn sw-btn--primary sw-btn--lg">
                    <?php esc_html_e( 'Przeglądaj sklep', 'secureware' ); ?>
                </a>
                <a href="#sw-categories" class="sw-btn sw-btn--secondary sw-btn--lg">
                    <?php esc_html_e( 'Kategorie', 'secureware' ); ?>
                </a>
            </div>

            <div class="sw-hero__stats">
                <div class="sw-hero__stat">
                    <div class="sw-hero__stat-value"><?php echo esc_html( get_theme_mod( 'secureware_stat_products', '500+' ) ); ?></div>
                    <div class="sw-hero__stat-label"><?php esc_html_e( 'Produktów', 'secureware' ); ?></div>
                </div>
                <div class="sw-hero__stat">
                    <div class="sw-hero__stat-value"><?php echo esc_html( get_theme_mod( 'secureware_stat_clients', '10k+' ) ); ?></div>
                    <div class="sw-hero__stat-label"><?php esc_html_e( 'Klientów', 'secureware' ); ?></div>
                </div>
                <div class="sw-hero__stat">
                    <div class="sw-hero__stat-value"><?php echo esc_html( get_theme_mod( 'secureware_stat_delivery', '< 1 min' ) ); ?></div>
                    <div class="sw-hero__stat-label"><?php esc_html_e( 'Dostawa', 'secureware' ); ?></div>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="sw-features">
    <div class="sw-container">
        <div class="sw-grid sw-grid-4">
            <div class="sw-feature-card">
                <div class="sw-feature-card__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                <h3 class="sw-feature-card__title"><?php esc_html_e( 'Natychmiastowa dostawa', 'secureware' ); ?></h3>
                <p class="sw-feature-card__desc"><?php esc_html_e( 'Klucz licencyjny na e-mail w kilka sekund po zakupie.', 'secureware' ); ?></p>
            </div>
            <div class="sw-feature-card">
                <div class="sw-feature-card__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <h3 class="sw-feature-card__title"><?php esc_html_e( '100% oryginalne', 'secureware' ); ?></h3>
                <p class="sw-feature-card__desc"><?php esc_html_e( 'Licencje od autoryzowanych dystrybutorów.', 'secureware' ); ?></p>
            </div>
            <div class="sw-feature-card">
                <div class="sw-feature-card__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                </div>
                <h3 class="sw-feature-card__title"><?php esc_html_e( 'Najlepsze ceny', 'secureware' ); ?></h3>
                <p class="sw-feature-card__desc"><?php esc_html_e( 'Konkurencyjne ceny i regularne promocje.', 'secureware' ); ?></p>
            </div>
            <div class="sw-feature-card">
                <div class="sw-feature-card__icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                </div>
                <h3 class="sw-feature-card__title"><?php esc_html_e( 'Wsparcie 24/7', 'secureware' ); ?></h3>
                <p class="sw-feature-card__desc"><?php esc_html_e( 'Pomoc z instalacją i aktywacją oprogramowania.', 'secureware' ); ?></p>
            </div>
        </div>
    </div>
</section>

<?php if ( class_exists( 'WooCommerce' ) ) : ?>
<section class="sw-categories" id="sw-categories">
    <div class="sw-container">
        <div class="sw-products__header">
            <h2><?php esc_html_e( 'Kategorie', 'secureware' ); ?></h2>
        </div>
        <div class="sw-grid sw-grid-3">
            <?php
            $categories = get_terms( array(
                'taxonomy'   => 'product_cat',
                'hide_empty' => true,
                'number'     => 6,
                'exclude'    => array( get_option( 'default_product_cat' ) ),
            ) );

            $category_icons = array(
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.26.604.852.997 1.51 1H21a2 2 0 0 1 0 4h-.09c-.66.003-1.25.396-1.51 1z"/></svg>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
            );

            if ( ! empty( $categories ) && ! is_wp_error( $categories ) ) :
                $i = 0;
                foreach ( $categories as $category ) :
                    $icon = $category_icons[ $i % count( $category_icons ) ];
                    $link = get_term_link( $category );
            ?>
                <a href="<?php echo esc_url( $link ); ?>" class="sw-category-card">
                    <div class="sw-category-card__icon">
                        <?php echo $icon; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </div>
                    <div>
                        <h3 class="sw-category-card__title"><?php echo esc_html( $category->name ); ?></h3>
                        <span class="sw-category-card__count">
                            <?php
                            echo esc_html( sprintf(
                                _n( '%d produkt', '%d produktów', $category->count, 'secureware' ),
                                $category->count
                            ) );
                            ?>
                        </span>
                    </div>
                </a>
            <?php
                    $i++;
                endforeach;
            else :
            ?>
                <div class="sw-category-card">
                    <div class="sw-category-card__icon"><?php echo $category_icons[0]; // phpcs:ignore ?></div>
                    <div>
                        <h3 class="sw-category-card__title"><?php esc_html_e( 'Systemy operacyjne', 'secureware' ); ?></h3>
                        <span class="sw-category-card__count"><?php esc_html_e( 'Windows, macOS', 'secureware' ); ?></span>
                    </div>
                </div>
                <div class="sw-category-card">
                    <div class="sw-category-card__icon"><?php echo $category_icons[1]; // phpcs:ignore ?></div>
                    <div>
                        <h3 class="sw-category-card__title"><?php esc_html_e( 'Antywirus', 'secureware' ); ?></h3>
                        <span class="sw-category-card__count"><?php esc_html_e( 'Norton, Kaspersky, ESET', 'secureware' ); ?></span>
                    </div>
                </div>
                <div class="sw-category-card">
                    <div class="sw-category-card__icon"><?php echo $category_icons[2]; // phpcs:ignore ?></div>
                    <div>
                        <h3 class="sw-category-card__title"><?php esc_html_e( 'Pakiety biurowe', 'secureware' ); ?></h3>
                        <span class="sw-category-card__count"><?php esc_html_e( 'Microsoft Office, Adobe', 'secureware' ); ?></span>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </div>
</section>

<section class="sw-products">
    <div class="sw-container">
        <div class="sw-products__header">
            <h2><?php esc_html_e( 'Polecane', 'secureware' ); ?></h2>
            <p><?php esc_html_e( 'Najpopularniejsze licencje w naszym sklepie', 'secureware' ); ?></p>
        </div>
        <?php echo do_shortcode( '[products limit="8" columns="4" orderby="popularity" visibility="featured"]' ); ?>
        <div class="sw-products__more">
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-btn sw-btn--secondary">
                <?php esc_html_e( 'Wszystkie produkty', 'secureware' ); ?>
            </a>
        </div>
    </div>
</section>

<section class="sw-products sw-products--alt">
    <div class="sw-container">
        <div class="sw-products__header">
            <h2><?php esc_html_e( 'Promocje', 'secureware' ); ?></h2>
            <p><?php esc_html_e( 'Aktualne obniżki cen', 'secureware' ); ?></p>
        </div>
        <?php echo do_shortcode( '[products limit="4" columns="4" on_sale="true" orderby="date"]' ); ?>
    </div>
</section>
<?php endif; ?>

<section class="sw-cta">
    <div class="sw-container">
        <div class="sw-cta__box">
            <h2 class="sw-cta__title"><?php echo esc_html( get_theme_mod( 'secureware_cta_title', __( 'Newsletter', 'secureware' ) ) ); ?></h2>
            <p class="sw-cta__desc"><?php echo esc_html( get_theme_mod( 'secureware_cta_description', __( 'Zapisz się i otrzymuj informacje o promocjach.', 'secureware' ) ) ); ?></p>
            <form class="sw-cta__form" action="#" method="post">
                <input type="email" name="email" placeholder="<?php esc_attr_e( 'adres@email.pl', 'secureware' ); ?>" required>
                <button type="submit" class="sw-btn sw-btn--primary"><?php esc_html_e( 'Zapisz', 'secureware' ); ?></button>
            </form>
        </div>
    </div>
</section>

<?php get_footer(); ?>
