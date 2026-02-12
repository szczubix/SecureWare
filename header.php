
<?php
/**
 * SecureWare - Header template
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<!-- Top info bar -->
<div class="sw-topbar">
    <div class="sw-container">
        <div class="sw-topbar__inner">
            <div class="sw-topbar__left">
                <span class="sw-topbar__item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                    <?php esc_html_e( 'Dostawa e-mail w 1 min', 'secureware' ); ?>
                </span>
                <span class="sw-topbar__item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    <?php esc_html_e( 'Oryginalne licencje', 'secureware' ); ?>
                </span>
                <span class="sw-topbar__item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    <?php esc_html_e( 'Ponad 10 000 klientów', 'secureware' ); ?>
                </span>
            </div>
            <div class="sw-topbar__right">
                <?php
                $company_phone = get_theme_mod( 'secureware_company_phone', '' );
                if ( $company_phone ) :
                ?>
                <a href="tel:<?php echo esc_attr( preg_replace( '/[^+0-9]/', '', $company_phone ) ); ?>" class="sw-topbar__item sw-topbar__item--link">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                    <?php echo esc_html( $company_phone ); ?>
                </a>
                <?php endif; ?>
                <a href="<?php echo esc_url( class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'myaccount' ) : '#' ); ?>" class="sw-topbar__item sw-topbar__item--link">
                    <?php esc_html_e( 'Pomoc', 'secureware' ); ?>
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Main header -->
<header class="sw-header" id="sw-header">
    <div class="sw-container">
        <div class="sw-header__inner">
            <!-- Logo -->
            <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="sw-header__logo" rel="home">
                <?php if ( has_custom_logo() ) : ?>
                    <?php
                    $logo_id  = get_theme_mod( 'custom_logo' );
                    $logo_url = wp_get_attachment_image_url( $logo_id, 'full' );
                    ?>
                    <img src="<?php echo esc_url( $logo_url ); ?>" alt="<?php bloginfo( 'name' ); ?>">
                <?php else : ?>
                    <svg width="30" height="30" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect width="32" height="32" rx="7" fill="#4f8fea"/>
                        <path d="M16 6L8 10v6c0 5.55 3.42 10.74 8 12 4.58-1.26 8-6.45 8-12v-6l-8-4z" fill="rgba(255,255,255,0.95)"/>
                        <path d="M14 16l2 2 4-4" stroke="#4f8fea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span><?php bloginfo( 'name' ); ?></span>
                <?php endif; ?>
            </a>

            <!-- Search bar -->
            <div class="sw-header__search">
                <form role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>" class="sw-search-form">
                    <input type="search" name="s" placeholder="<?php esc_attr_e( 'Czego szukasz? np. Windows 11, Office 365, Norton...', 'secureware' ); ?>" value="<?php echo get_search_query(); ?>" autocomplete="off">
                    <?php if ( class_exists( 'WooCommerce' ) ) : ?>
                        <input type="hidden" name="post_type" value="product">
                    <?php endif; ?>
                    <button type="submit" class="sw-search-form__btn" aria-label="<?php esc_attr_e( 'Szukaj', 'secureware' ); ?>">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    </button>
                </form>
            </div>

            <!-- Header actions -->
            <div class="sw-header__actions">
                <?php if ( class_exists( 'WooCommerce' ) ) : ?>
                <a href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" class="sw-header__action">
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <span class="sw-header__action-label"><?php esc_html_e( 'Konto', 'secureware' ); ?></span>
                </a>
                <a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="sw-header__action sw-header__action--cart">
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                    <span class="sw-header__action-label"><?php esc_html_e( 'Koszyk', 'secureware' ); ?></span>
                    <span class="sw-header__cart-count"><?php echo esc_html( WC()->cart->get_cart_contents_count() ); ?></span>
                </a>
                <?php endif; ?>
            </div>

            <!-- Mobile toggle -->
            <button class="sw-menu-toggle" id="sw-menu-toggle" aria-label="<?php esc_attr_e( 'Menu', 'secureware' ); ?>">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
        </div>
    </div>

    <!-- Category navigation -->
    <nav class="sw-catnav" id="sw-catnav" role="navigation" aria-label="<?php esc_attr_e( 'Nawigacja', 'secureware' ); ?>">
        <div class="sw-container">
            <div class="sw-catnav__inner">
                <?php
                if ( has_nav_menu( 'primary' ) ) {
                    wp_nav_menu( array(
                        'theme_location' => 'primary',
                        'menu_class'     => 'sw-catnav__menu',
                        'container'      => false,
                        'depth'          => 2,
                        'fallback_cb'    => false,
                    ) );
                } elseif ( class_exists( 'WooCommerce' ) ) {
                    // Fallback: show product categories
                    $cats = get_terms( array(
                        'taxonomy'   => 'product_cat',
                        'hide_empty' => true,
                        'number'     => 8,
                        'exclude'    => array( get_option( 'default_product_cat' ) ),
                    ) );
                    if ( ! empty( $cats ) && ! is_wp_error( $cats ) ) {
                        echo '<ul class="sw-catnav__menu">';
                        foreach ( $cats as $cat ) {
                            echo '<li><a href="' . esc_url( get_term_link( $cat ) ) . '">' . esc_html( $cat->name ) . '</a></li>';
                        }
                        echo '</ul>';
                    }
                }
                ?>
            </div>
        </div>
    </nav>
</header>

<main id="sw-main" class="sw-main">
