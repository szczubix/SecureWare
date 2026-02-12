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

<div id="sw-wrapper">

<header class="sw-header" id="sw-header">
    <div class="sw-header__bar">
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
                        <div class="sw-header__logo-icon">
                            <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M16 3L6 8v8c0 7.4 4.56 14.32 10 16 5.44-1.68 10-8.6 10-16V8L16 3z" fill="currentColor" opacity="0.15"/>
                                <path d="M16 3L6 8v8c0 7.4 4.56 14.32 10 16 5.44-1.68 10-8.6 10-16V8L16 3z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                <path d="M12 16l3 3 5-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <span><?php bloginfo( 'name' ); ?></span>
                    <?php endif; ?>
                </a>

                <!-- Navigation -->
                <nav class="sw-header__nav" id="sw-nav">
                    <?php
                    if ( has_nav_menu( 'primary' ) ) {
                        wp_nav_menu( array(
                            'theme_location' => 'primary',
                            'menu_class'     => 'sw-nav',
                            'container'      => false,
                            'depth'          => 2,
                            'fallback_cb'    => false,
                        ) );
                    } elseif ( class_exists( 'WooCommerce' ) ) {
                        echo '<ul class="sw-nav">';
                        echo '<li><a href="' . esc_url( wc_get_page_permalink( 'shop' ) ) . '">' . esc_html__( 'Sklep', 'secureware' ) . '</a></li>';
                        $cats = get_terms( array(
                            'taxonomy'   => 'product_cat',
                            'hide_empty' => true,
                            'number'     => 5,
                            'exclude'    => array( get_option( 'default_product_cat' ) ),
                        ) );
                        if ( ! empty( $cats ) && ! is_wp_error( $cats ) ) {
                            foreach ( $cats as $cat ) {
                                echo '<li><a href="' . esc_url( get_term_link( $cat ) ) . '">' . esc_html( $cat->name ) . '</a></li>';
                            }
                        }
                        echo '</ul>';
                    }
                    ?>
                </nav>

                <!-- Right side -->
                <div class="sw-header__right">
                    <div class="sw-header__search" id="sw-search">
                        <button type="button" class="sw-header__search-toggle" id="sw-search-toggle" aria-label="<?php esc_attr_e( 'Szukaj', 'secureware' ); ?>">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                            <span class="sw-header__search-label"><?php esc_html_e( 'SZUKAJ', 'secureware' ); ?></span>
                        </button>
                        <div class="sw-header__search-form" id="sw-search-form">
                            <form role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
                                <input type="search" name="s" placeholder="<?php esc_attr_e( 'Wpisz nazwę produktu...', 'secureware' ); ?>" value="<?php echo get_search_query(); ?>" autocomplete="off">
                                <?php if ( class_exists( 'WooCommerce' ) ) : ?>
                                    <input type="hidden" name="post_type" value="product">
                                <?php endif; ?>
                                <button type="submit" aria-label="<?php esc_attr_e( 'Szukaj', 'secureware' ); ?>">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                                </button>
                            </form>
                        </div>
                    </div>

                    <?php if ( class_exists( 'WooCommerce' ) ) : ?>
                    <a href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" class="sw-header__icon" aria-label="<?php esc_attr_e( 'Konto', 'secureware' ); ?>">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    </a>
                    <a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="sw-header__icon sw-header__icon--cart">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                        <?php $count = WC()->cart->get_cart_contents_count(); ?>
                        <?php if ( $count > 0 ) : ?>
                            <span class="sw-header__cart-count"><?php echo esc_html( $count ); ?></span>
                        <?php endif; ?>
                    </a>
                    <?php endif; ?>

                    <button class="sw-header__burger" id="sw-burger" aria-label="<?php esc_attr_e( 'Menu', 'secureware' ); ?>">
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</header>

<main id="sw-main" class="sw-main">
