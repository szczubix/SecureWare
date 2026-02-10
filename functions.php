<?php
/**
 * SecureWare - Functions and definitions
 *
 * @package SecureWare
 * @version 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'SECUREWARE_VERSION', '1.0.0' );
define( 'SECUREWARE_DIR', get_template_directory() );
define( 'SECUREWARE_URI', get_template_directory_uri() );

/**
 * Theme Setup
 */
function secureware_setup() {
    load_theme_textdomain( 'secureware', SECUREWARE_DIR . '/languages' );

    add_theme_support( 'automatic-feed-links' );
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ) );
    add_theme_support( 'customize-selective-refresh-widgets' );

    // WooCommerce support
    add_theme_support( 'woocommerce', array(
        'thumbnail_image_width' => 400,
        'single_image_width'    => 600,
        'product_grid'          => array(
            'default_rows'    => 3,
            'min_rows'        => 1,
            'default_columns' => 3,
            'min_columns'     => 1,
            'max_columns'     => 4,
        ),
    ) );
    add_theme_support( 'wc-product-gallery-zoom' );
    add_theme_support( 'wc-product-gallery-lightbox' );
    add_theme_support( 'wc-product-gallery-slider' );

    // Custom logo
    add_theme_support( 'custom-logo', array(
        'height'      => 80,
        'width'       => 250,
        'flex-height' => true,
        'flex-width'  => true,
    ) );

    // Image sizes
    add_image_size( 'secureware-product-thumb', 400, 250, true );
    add_image_size( 'secureware-product-large', 800, 500, true );
    add_image_size( 'secureware-hero', 1920, 800, true );

    // Navigation menus
    register_nav_menus( array(
        'primary'    => esc_html__( 'Menu główne', 'secureware' ),
        'footer-1'   => esc_html__( 'Stopka - Kolumna 1', 'secureware' ),
        'footer-2'   => esc_html__( 'Stopka - Kolumna 2', 'secureware' ),
        'footer-3'   => esc_html__( 'Stopka - Kolumna 3', 'secureware' ),
    ) );
}
add_action( 'after_setup_theme', 'secureware_setup' );

/**
 * Enqueue scripts and styles
 */
function secureware_scripts() {
    // Google Fonts - Inter & JetBrains Mono
    wp_enqueue_style(
        'secureware-google-fonts',
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap',
        array(),
        null
    );

    // Main stylesheet
    wp_enqueue_style(
        'secureware-main',
        SECUREWARE_URI . '/assets/css/main.css',
        array(),
        SECUREWARE_VERSION
    );

    // Theme stylesheet (style.css)
    wp_enqueue_style(
        'secureware-style',
        get_stylesheet_uri(),
        array( 'secureware-main' ),
        SECUREWARE_VERSION
    );

    // Main JavaScript
    wp_enqueue_script(
        'secureware-main',
        SECUREWARE_URI . '/assets/js/main.js',
        array(),
        SECUREWARE_VERSION,
        true
    );

    // Localize script
    wp_localize_script( 'secureware-main', 'securewareData', array(
        'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
        'nonce'    => wp_create_nonce( 'secureware_nonce' ),
        'strings'  => array(
            'copied'       => esc_html__( 'Skopiowano!', 'secureware' ),
            'copyKey'      => esc_html__( 'Kopiuj klucz', 'secureware' ),
            'addedToCart'  => esc_html__( 'Dodano do koszyka', 'secureware' ),
        ),
    ) );

    // WooCommerce styles
    if ( class_exists( 'WooCommerce' ) ) {
        wp_enqueue_style(
            'secureware-woocommerce',
            SECUREWARE_URI . '/assets/css/woocommerce.css',
            array( 'secureware-main' ),
            SECUREWARE_VERSION
        );
    }
}
add_action( 'wp_enqueue_scripts', 'secureware_scripts' );

/**
 * Register widget areas
 */
function secureware_widgets_init() {
    register_sidebar( array(
        'name'          => esc_html__( 'Sidebar sklepu', 'secureware' ),
        'id'            => 'shop-sidebar',
        'description'   => esc_html__( 'Widgety wyświetlane na stronie sklepu.', 'secureware' ),
        'before_widget' => '<div id="%1$s" class="sw-widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h3 class="sw-widget__title">',
        'after_title'   => '</h3>',
    ) );

    register_sidebar( array(
        'name'          => esc_html__( 'Stopka - Kolumna dodatkowa', 'secureware' ),
        'id'            => 'footer-extra',
        'description'   => esc_html__( 'Widgety dodatkowe w stopce.', 'secureware' ),
        'before_widget' => '<div id="%1$s" class="sw-footer-widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="sw-footer__heading">',
        'after_title'   => '</h4>',
    ) );
}
add_action( 'widgets_init', 'secureware_widgets_init' );

/**
 * WooCommerce hooks and customizations
 */
if ( class_exists( 'WooCommerce' ) ) {
    // Change number of products per page
    add_filter( 'loop_shop_per_page', function() {
        return 12;
    } );

    // Disable default WooCommerce styles
    add_filter( 'woocommerce_enqueue_styles', function( $styles ) {
        unset( $styles['woocommerce-general'] );
        return $styles;
    } );

    // Add wrapper around product loop items
    remove_action( 'woocommerce_before_shop_loop_item', 'woocommerce_template_loop_product_link_open', 10 );
    remove_action( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_product_link_close', 5 );

    // Customize product badge text
    add_filter( 'woocommerce_sale_flash', function() {
        return '<span class="onsale">' . esc_html__( 'Promocja', 'secureware' ) . '</span>';
    } );
}

/**
 * AJAX cart fragment for header cart count
 */
function secureware_cart_count_fragment( $fragments ) {
    if ( class_exists( 'WooCommerce' ) ) {
        $count = WC()->cart->get_cart_contents_count();
        $fragments['.sw-header__cart-count'] = '<span class="sw-header__cart-count">' . esc_html( $count ) . '</span>';
    }
    return $fragments;
}
add_filter( 'woocommerce_add_to_cart_fragments', 'secureware_cart_count_fragment' );

/**
 * Custom WooCommerce My Account endpoint for licenses
 */
function secureware_add_license_endpoint() {
    add_rewrite_endpoint( 'my-licenses', EP_ROOT | EP_PAGES );
}
add_action( 'init', 'secureware_add_license_endpoint' );

function secureware_license_query_vars( $vars ) {
    $vars[] = 'my-licenses';
    return $vars;
}
add_filter( 'query_vars', 'secureware_license_query_vars' );

function secureware_add_license_link_my_account( $items ) {
    $new_items = array();
    foreach ( $items as $key => $value ) {
        $new_items[ $key ] = $value;
        if ( 'orders' === $key ) {
            $new_items['my-licenses'] = esc_html__( 'Moje licencje', 'secureware' );
        }
    }
    return $new_items;
}
add_filter( 'woocommerce_account_menu_items', 'secureware_add_license_link_my_account' );

function secureware_license_endpoint_content() {
    wc_get_template(
        'myaccount/my-licenses.php',
        array(),
        '',
        SECUREWARE_DIR . '/woocommerce/'
    );
}
add_action( 'woocommerce_account_my-licenses_endpoint', 'secureware_license_endpoint_content' );

/**
 * Include theme components
 */
require_once SECUREWARE_DIR . '/inc/customizer.php';
require_once SECUREWARE_DIR . '/inc/license-manager.php';
require_once SECUREWARE_DIR . '/inc/template-tags.php';

/**
 * Flush rewrite rules on theme activation
 */
function secureware_activate() {
    secureware_add_license_endpoint();
    flush_rewrite_rules();
}
add_action( 'after_switch_theme', 'secureware_activate' );
