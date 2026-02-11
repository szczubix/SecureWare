
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

<header class="sw-header" id="sw-header">
    <!-- Top row: search | logo | cart+account -->
    <div class="sw-header__top">
        <div class="sw-header__top-inner">
            <div class="sw-header__top-left">
                <div class="sw-header__search">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <form role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
                        <input type="search" name="s" placeholder="<?php esc_attr_e( 'Szukaj...', 'secureware' ); ?>" value="<?php echo get_search_query(); ?>">
                        <?php if ( class_exists( 'WooCommerce' ) ) : ?>
                            <input type="hidden" name="post_type" value="product">
                        <?php endif; ?>
                    </form>
                </div>
            </div>

            <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="sw-header__logo" rel="home">
                <?php if ( has_custom_logo() ) : ?>
                    <?php
                    $logo_id  = get_theme_mod( 'custom_logo' );
                    $logo_url = wp_get_attachment_image_url( $logo_id, 'full' );
                    ?>
                    <img src="<?php echo esc_url( $logo_url ); ?>" alt="<?php bloginfo( 'name' ); ?>">
                <?php else : ?>
                    <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect width="32" height="32" rx="7" fill="#4f8fea"/>
                        <path d="M16 6L8 10v6c0 5.55 3.42 10.74 8 12 4.58-1.26 8-6.45 8-12v-6l-8-4z" fill="rgba(255,255,255,0.95)"/>
                        <path d="M14 16l2 2 4-4" stroke="#4f8fea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span><?php bloginfo( 'name' ); ?></span>
                <?php endif; ?>
            </a>

            <div class="sw-header__top-right">
                <?php if ( class_exists( 'WooCommerce' ) ) : ?>
                    <a href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" class="sw-header__icon-link" title="<?php esc_attr_e( 'Moje konto', 'secureware' ); ?>">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    </a>
                    <a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="sw-header__icon-link sw-header__cart" title="<?php esc_attr_e( 'Koszyk', 'secureware' ); ?>">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                        <span class="sw-header__cart-count"><?php echo esc_html( WC()->cart->get_cart_contents_count() ); ?></span>
                    </a>
                <?php endif; ?>
                <button class="sw-menu-toggle" id="sw-menu-toggle" aria-label="<?php esc_attr_e( 'Otwórz menu', 'secureware' ); ?>">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
                </button>
            </div>
        </div>
    </div>

    <!-- Bottom row: navigation menu -->
    <nav class="sw-header__nav" role="navigation" aria-label="<?php esc_attr_e( 'Menu główne', 'secureware' ); ?>">
        <div class="sw-header__nav-inner">
            <?php
            if ( has_nav_menu( 'primary' ) ) {
                wp_nav_menu( array(
                    'theme_location' => 'primary',
                    'menu_class'     => 'sw-nav__menu',
                    'container'      => false,
                    'depth'          => 2,
                    'fallback_cb'    => false,
                ) );
            }
            ?>
        </div>
    </nav>
</header>

<main id="sw-main" class="sw-main">
