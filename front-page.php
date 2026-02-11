<?php
/**
 * SecureWare - Front Page Template
 *
 * @package SecureWare
 */

get_header();
?>

<!-- Trust bar -->
<div class="sw-trustbar">
    <div class="sw-container">
        <div class="sw-trustbar__inner">
            <div class="sw-trustbar__item">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                <?php esc_html_e( 'Natychmiastowa dostawa', 'secureware' ); ?>
            </div>
            <div class="sw-trustbar__item">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                <?php esc_html_e( '100% oryginalne licencje', 'secureware' ); ?>
            </div>
            <div class="sw-trustbar__item">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <?php esc_html_e( 'Wsparcie techniczne 24/7', 'secureware' ); ?>
            </div>
            <div class="sw-trustbar__item">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                <?php esc_html_e( 'Najlepsze ceny', 'secureware' ); ?>
            </div>
        </div>
    </div>
</div>

<?php if ( class_exists( 'WooCommerce' ) ) : ?>

<!-- Categories -->
<section class="sw-categories">
    <div class="sw-container">
        <div class="sw-section-header">
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
                <a href="<?php echo esc_url( class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'shop' ) : '#' ); ?>" class="sw-category-card">
                    <div class="sw-category-card__icon"><?php echo $category_icons[0]; // phpcs:ignore ?></div>
                    <div>
                        <h3 class="sw-category-card__title"><?php esc_html_e( 'Systemy operacyjne', 'secureware' ); ?></h3>
                        <span class="sw-category-card__count"><?php esc_html_e( 'Windows, macOS', 'secureware' ); ?></span>
                    </div>
                </a>
                <a href="<?php echo esc_url( class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'shop' ) : '#' ); ?>" class="sw-category-card">
                    <div class="sw-category-card__icon"><?php echo $category_icons[1]; // phpcs:ignore ?></div>
                    <div>
                        <h3 class="sw-category-card__title"><?php esc_html_e( 'Antywirus', 'secureware' ); ?></h3>
                        <span class="sw-category-card__count"><?php esc_html_e( 'Norton, Kaspersky, ESET', 'secureware' ); ?></span>
                    </div>
                </a>
                <a href="<?php echo esc_url( class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'shop' ) : '#' ); ?>" class="sw-category-card">
                    <div class="sw-category-card__icon"><?php echo $category_icons[2]; // phpcs:ignore ?></div>
                    <div>
                        <h3 class="sw-category-card__title"><?php esc_html_e( 'Pakiety biurowe', 'secureware' ); ?></h3>
                        <span class="sw-category-card__count"><?php esc_html_e( 'Microsoft Office, Adobe', 'secureware' ); ?></span>
                    </div>
                </a>
            <?php endif; ?>
        </div>
    </div>
</section>

<!-- Featured products -->
<section class="sw-products">
    <div class="sw-container">
        <div class="sw-section-header">
            <h2><?php esc_html_e( 'Polecane', 'secureware' ); ?></h2>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-section-header__link">
                <?php esc_html_e( 'Zobacz wszystkie', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <?php echo do_shortcode( '[products limit="8" columns="4" orderby="popularity" visibility="featured"]' ); ?>
    </div>
</section>

<!-- Sale products -->
<section class="sw-products sw-products--alt">
    <div class="sw-container">
        <div class="sw-section-header">
            <h2><?php esc_html_e( 'Promocje', 'secureware' ); ?></h2>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>?on_sale=1" class="sw-section-header__link">
                <?php esc_html_e( 'Wszystkie promocje', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <?php echo do_shortcode( '[products limit="4" columns="4" on_sale="true" orderby="date"]' ); ?>
    </div>
</section>

<!-- Latest products -->
<section class="sw-products">
    <div class="sw-container">
        <div class="sw-section-header">
            <h2><?php esc_html_e( 'Nowości', 'secureware' ); ?></h2>
            <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>?orderby=date" class="sw-section-header__link">
                <?php esc_html_e( 'Zobacz wszystkie', 'secureware' ); ?>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
        </div>
        <?php echo do_shortcode( '[products limit="4" columns="4" orderby="date"]' ); ?>
    </div>
</section>

<?php endif; ?>

<!-- Newsletter CTA -->
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
