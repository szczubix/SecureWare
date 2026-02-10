<?php
/**
 * SecureWare - Theme Customizer
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Register Customizer settings.
 *
 * @param WP_Customize_Manager $wp_customize Theme Customizer object.
 */
function secureware_customize_register( $wp_customize ) {

    // =============================================
    // Section: Hero
    // =============================================
    $wp_customize->add_section( 'secureware_hero', array(
        'title'    => __( 'Sekcja Hero', 'secureware' ),
        'priority' => 30,
    ) );

    $wp_customize->add_setting( 'secureware_hero_title', array(
        'default'           => __( 'Oryginalne licencje na <span>oprogramowanie</span>', 'secureware' ),
        'sanitize_callback' => 'wp_kses_post',
    ) );
    $wp_customize->add_control( 'secureware_hero_title', array(
        'label'   => __( 'Tytuł Hero', 'secureware' ),
        'section' => 'secureware_hero',
        'type'    => 'textarea',
    ) );

    $wp_customize->add_setting( 'secureware_hero_description', array(
        'default'           => __( 'Kup licencje na najlepsze oprogramowanie w najniższych cenach. Natychmiastowa dostawa kluczy na e-mail.', 'secureware' ),
        'sanitize_callback' => 'sanitize_text_field',
    ) );
    $wp_customize->add_control( 'secureware_hero_description', array(
        'label'   => __( 'Opis Hero', 'secureware' ),
        'section' => 'secureware_hero',
        'type'    => 'textarea',
    ) );

    // Stats
    $stats = array(
        'products' => array( 'label' => __( 'Statystyka: Produkty', 'secureware' ), 'default' => '500+' ),
        'clients'  => array( 'label' => __( 'Statystyka: Klienci', 'secureware' ), 'default' => '10k+' ),
        'delivery' => array( 'label' => __( 'Statystyka: Czas dostawy', 'secureware' ), 'default' => '< 1 min' ),
        'support'  => array( 'label' => __( 'Statystyka: Wsparcie', 'secureware' ), 'default' => '24/7' ),
    );

    foreach ( $stats as $key => $data ) {
        $wp_customize->add_setting( "secureware_stat_{$key}", array(
            'default'           => $data['default'],
            'sanitize_callback' => 'sanitize_text_field',
        ) );
        $wp_customize->add_control( "secureware_stat_{$key}", array(
            'label'   => $data['label'],
            'section' => 'secureware_hero',
            'type'    => 'text',
        ) );
    }

    // =============================================
    // Section: Dane firmy (footer)
    // =============================================
    $wp_customize->add_section( 'secureware_company', array(
        'title'    => __( 'Dane firmy (stopka)', 'secureware' ),
        'priority' => 35,
    ) );

    $company_fields = array(
        'company_name'    => array( 'label' => __( 'Nazwa firmy', 'secureware' ), 'default' => '' ),
        'company_nip'     => array( 'label' => __( 'NIP', 'secureware' ), 'default' => '' ),
        'company_regon'   => array( 'label' => __( 'REGON', 'secureware' ), 'default' => '' ),
        'company_address' => array( 'label' => __( 'Adres', 'secureware' ), 'default' => '' ),
        'company_email'   => array( 'label' => __( 'E-mail kontaktowy', 'secureware' ), 'default' => '' ),
        'company_phone'   => array( 'label' => __( 'Telefon', 'secureware' ), 'default' => '' ),
    );

    foreach ( $company_fields as $key => $data ) {
        $wp_customize->add_setting( "secureware_{$key}", array(
            'default'           => $data['default'],
            'sanitize_callback' => 'sanitize_text_field',
        ) );
        $wp_customize->add_control( "secureware_{$key}", array(
            'label'   => $data['label'],
            'section' => 'secureware_company',
            'type'    => 'text',
        ) );
    }

    // =============================================
    // Section: Stopka - Ustawienia
    // =============================================
    $wp_customize->add_section( 'secureware_footer', array(
        'title'    => __( 'Stopka - Ustawienia', 'secureware' ),
        'priority' => 36,
    ) );

    $wp_customize->add_setting( 'secureware_footer_description', array(
        'default'           => __( 'Twój zaufany dostawca licencji na oprogramowanie. Oferujemy oryginalne klucze w najlepszych cenach.', 'secureware' ),
        'sanitize_callback' => 'sanitize_text_field',
    ) );
    $wp_customize->add_control( 'secureware_footer_description', array(
        'label'   => __( 'Opis w stopce', 'secureware' ),
        'section' => 'secureware_footer',
        'type'    => 'textarea',
    ) );

    // Footer column titles
    $footer_cols = array(
        'col1' => array( 'label' => __( 'Nagłówek kolumny 1', 'secureware' ), 'default' => __( 'Produkty', 'secureware' ) ),
        'col2' => array( 'label' => __( 'Nagłówek kolumny 2', 'secureware' ), 'default' => __( 'Informacje', 'secureware' ) ),
        'col3' => array( 'label' => __( 'Nagłówek kolumny 3', 'secureware' ), 'default' => __( 'Pomoc', 'secureware' ) ),
    );

    foreach ( $footer_cols as $key => $data ) {
        $wp_customize->add_setting( "secureware_footer_{$key}_title", array(
            'default'           => $data['default'],
            'sanitize_callback' => 'sanitize_text_field',
        ) );
        $wp_customize->add_control( "secureware_footer_{$key}_title", array(
            'label'   => $data['label'],
            'section' => 'secureware_footer',
            'type'    => 'text',
        ) );
    }

    $wp_customize->add_setting( 'secureware_payment_methods', array(
        'default'           => 'visa,mastercard,blik,przelewy24',
        'sanitize_callback' => 'sanitize_text_field',
    ) );
    $wp_customize->add_control( 'secureware_payment_methods', array(
        'label'       => __( 'Metody płatności (oddzielone przecinkami)', 'secureware' ),
        'section'     => 'secureware_footer',
        'type'        => 'text',
        'description' => __( 'np. visa,mastercard,blik,przelewy24', 'secureware' ),
    ) );

    // =============================================
    // Section: Social Media
    // =============================================
    $wp_customize->add_section( 'secureware_social', array(
        'title'    => __( 'Social Media', 'secureware' ),
        'priority' => 37,
    ) );

    $social_networks = array(
        'facebook'  => 'Facebook',
        'twitter'   => 'X (Twitter)',
        'instagram' => 'Instagram',
        'linkedin'  => 'LinkedIn',
    );

    foreach ( $social_networks as $key => $label ) {
        $wp_customize->add_setting( "secureware_social_{$key}", array(
            'default'           => '',
            'sanitize_callback' => 'esc_url_raw',
        ) );
        $wp_customize->add_control( "secureware_social_{$key}", array(
            'label'   => $label . ' URL',
            'section' => 'secureware_social',
            'type'    => 'url',
        ) );
    }

    // =============================================
    // Section: CTA / Newsletter
    // =============================================
    $wp_customize->add_section( 'secureware_cta', array(
        'title'    => __( 'Newsletter / CTA', 'secureware' ),
        'priority' => 38,
    ) );

    $wp_customize->add_setting( 'secureware_cta_title', array(
        'default'           => __( 'Bądź na bieżąco z promocjami', 'secureware' ),
        'sanitize_callback' => 'sanitize_text_field',
    ) );
    $wp_customize->add_control( 'secureware_cta_title', array(
        'label'   => __( 'Tytuł CTA', 'secureware' ),
        'section' => 'secureware_cta',
        'type'    => 'text',
    ) );

    $wp_customize->add_setting( 'secureware_cta_description', array(
        'default'           => __( 'Zapisz się do newslettera i otrzymuj informacje o najnowszych promocjach i produktach.', 'secureware' ),
        'sanitize_callback' => 'sanitize_text_field',
    ) );
    $wp_customize->add_control( 'secureware_cta_description', array(
        'label'   => __( 'Opis CTA', 'secureware' ),
        'section' => 'secureware_cta',
        'type'    => 'textarea',
    ) );
}
add_action( 'customize_register', 'secureware_customize_register' );
