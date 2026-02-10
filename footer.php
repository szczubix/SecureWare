<?php
/**
 * SecureWare - Footer template (customizowalna stopka)
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>
</main><!-- #sw-main -->

<footer class="sw-footer" id="sw-footer">
    <div class="sw-container">
        <div class="sw-footer__grid">
            <!-- Brand Column -->
            <div class="sw-footer__brand">
                <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="sw-header__logo">
                    <?php if ( has_custom_logo() ) : ?>
                        <?php
                        $logo_id  = get_theme_mod( 'custom_logo' );
                        $logo_url = wp_get_attachment_image_url( $logo_id, 'full' );
                        ?>
                        <img src="<?php echo esc_url( $logo_url ); ?>" alt="<?php bloginfo( 'name' ); ?>">
                    <?php else : ?>
                        <span><?php bloginfo( 'name' ); ?></span>
                    <?php endif; ?>
                </a>
                <p><?php echo esc_html( get_theme_mod( 'secureware_footer_description', __( 'Twój zaufany dostawca licencji na oprogramowanie. Oferujemy oryginalne klucze w najlepszych cenach.', 'secureware' ) ) ); ?></p>

                <!-- Social Media -->
                <div class="sw-footer__social">
                    <?php
                    $social_links = array(
                        'facebook'  => get_theme_mod( 'secureware_social_facebook', '' ),
                        'twitter'   => get_theme_mod( 'secureware_social_twitter', '' ),
                        'instagram' => get_theme_mod( 'secureware_social_instagram', '' ),
                        'linkedin'  => get_theme_mod( 'secureware_social_linkedin', '' ),
                    );

                    $social_icons = array(
                        'facebook'  => '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
                        'twitter'   => '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
                        'instagram' => '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>',
                        'linkedin'  => '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
                    );

                    foreach ( $social_links as $network => $url ) :
                        if ( ! empty( $url ) ) :
                    ?>
                        <a href="<?php echo esc_url( $url ); ?>" target="_blank" rel="noopener noreferrer" aria-label="<?php echo esc_attr( ucfirst( $network ) ); ?>">
                            <?php echo $social_icons[ $network ]; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                        </a>
                    <?php
                        endif;
                    endforeach;
                    ?>
                </div>
            </div>

            <!-- Footer Menu Columns -->
            <?php if ( has_nav_menu( 'footer-1' ) ) : ?>
            <div class="sw-footer__col">
                <h4 class="sw-footer__heading"><?php echo esc_html( get_theme_mod( 'secureware_footer_col1_title', __( 'Produkty', 'secureware' ) ) ); ?></h4>
                <?php
                wp_nav_menu( array(
                    'theme_location' => 'footer-1',
                    'menu_class'     => 'sw-footer__links',
                    'container'      => false,
                    'depth'          => 1,
                    'fallback_cb'    => false,
                ) );
                ?>
            </div>
            <?php endif; ?>

            <?php if ( has_nav_menu( 'footer-2' ) ) : ?>
            <div class="sw-footer__col">
                <h4 class="sw-footer__heading"><?php echo esc_html( get_theme_mod( 'secureware_footer_col2_title', __( 'Informacje', 'secureware' ) ) ); ?></h4>
                <?php
                wp_nav_menu( array(
                    'theme_location' => 'footer-2',
                    'menu_class'     => 'sw-footer__links',
                    'container'      => false,
                    'depth'          => 1,
                    'fallback_cb'    => false,
                ) );
                ?>
            </div>
            <?php endif; ?>

            <?php if ( has_nav_menu( 'footer-3' ) ) : ?>
            <div class="sw-footer__col">
                <h4 class="sw-footer__heading"><?php echo esc_html( get_theme_mod( 'secureware_footer_col3_title', __( 'Pomoc', 'secureware' ) ) ); ?></h4>
                <?php
                wp_nav_menu( array(
                    'theme_location' => 'footer-3',
                    'menu_class'     => 'sw-footer__links',
                    'container'      => false,
                    'depth'          => 1,
                    'fallback_cb'    => false,
                ) );
                ?>
            </div>
            <?php endif; ?>
        </div>

        <!-- Company Info (Customizer) -->
        <?php
        $company_name    = get_theme_mod( 'secureware_company_name', '' );
        $company_nip     = get_theme_mod( 'secureware_company_nip', '' );
        $company_regon   = get_theme_mod( 'secureware_company_regon', '' );
        $company_address = get_theme_mod( 'secureware_company_address', '' );
        $company_email   = get_theme_mod( 'secureware_company_email', '' );
        $company_phone   = get_theme_mod( 'secureware_company_phone', '' );

        if ( $company_name || $company_nip || $company_address ) :
        ?>
        <div class="sw-footer__company">
            <div class="sw-footer__company-inner">
                <?php if ( $company_name ) : ?>
                    <span class="sw-footer__company-item">
                        <strong><?php echo esc_html( $company_name ); ?></strong>
                    </span>
                <?php endif; ?>
                <?php if ( $company_nip ) : ?>
                    <span class="sw-footer__company-item">
                        NIP: <?php echo esc_html( $company_nip ); ?>
                    </span>
                <?php endif; ?>
                <?php if ( $company_regon ) : ?>
                    <span class="sw-footer__company-item">
                        REGON: <?php echo esc_html( $company_regon ); ?>
                    </span>
                <?php endif; ?>
                <?php if ( $company_address ) : ?>
                    <span class="sw-footer__company-item">
                        <?php echo esc_html( $company_address ); ?>
                    </span>
                <?php endif; ?>
                <?php if ( $company_email ) : ?>
                    <span class="sw-footer__company-item">
                        <a href="mailto:<?php echo esc_attr( $company_email ); ?>"><?php echo esc_html( $company_email ); ?></a>
                    </span>
                <?php endif; ?>
                <?php if ( $company_phone ) : ?>
                    <span class="sw-footer__company-item">
                        <a href="tel:<?php echo esc_attr( preg_replace( '/[^+0-9]/', '', $company_phone ) ); ?>"><?php echo esc_html( $company_phone ); ?></a>
                    </span>
                <?php endif; ?>
            </div>
        </div>
        <?php endif; ?>

        <!-- Bottom Bar -->
        <div class="sw-footer__bottom">
            <div class="sw-footer__copyright">
                <?php
                echo esc_html( sprintf(
                    /* translators: 1: current year, 2: site name */
                    __( '© %1$s %2$s. Wszelkie prawa zastrzeżone.', 'secureware' ),
                    date( 'Y' ),
                    get_bloginfo( 'name' )
                ) );
                ?>
            </div>
            <div class="sw-footer__payments">
                <?php
                $payment_methods = get_theme_mod( 'secureware_payment_methods', 'visa,mastercard,blik,przelewy24' );
                if ( $payment_methods ) :
                    $methods = array_map( 'trim', explode( ',', $payment_methods ) );
                    foreach ( $methods as $method ) :
                ?>
                    <span class="sw-footer__payment-badge"><?php echo esc_html( strtoupper( $method ) ); ?></span>
                <?php
                    endforeach;
                endif;
                ?>
            </div>
        </div>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
