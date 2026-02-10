<?php
/**
 * SecureWare - Template Tags
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Display product license badge if product is a license product.
 *
 * @param int $product_id Product ID.
 */
function secureware_license_badge( $product_id = null ) {
    if ( ! $product_id ) {
        $product_id = get_the_ID();
    }

    $is_license = get_post_meta( $product_id, '_secureware_is_license', true );
    if ( 'yes' === $is_license ) {
        echo '<span class="sw-product-card__badge">';
        esc_html_e( 'Licencja cyfrowa', 'secureware' );
        echo '</span>';
    }
}

/**
 * Display product delivery info.
 */
function secureware_delivery_info() {
    $product_id = get_the_ID();
    $is_license = get_post_meta( $product_id, '_secureware_is_license', true );

    if ( 'yes' !== $is_license ) {
        return;
    }

    $expiry_days = get_post_meta( $product_id, '_secureware_license_expiry_days', true );
    ?>
    <div class="sw-delivery-info" style="margin: 1.5rem 0; padding: 1rem 1.25rem; background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.15); border-radius: var(--sw-radius);">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; color: var(--sw-accent); font-weight: 600;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <?php esc_html_e( 'Natychmiastowa dostawa cyfrowa', 'secureware' ); ?>
        </div>
        <p style="margin: 0; font-size: 0.85rem; color: var(--sw-text-muted);">
            <?php esc_html_e( 'Klucz licencyjny zostanie wysłany na Twój e-mail natychmiast po zakupie.', 'secureware' ); ?>
        </p>
        <?php if ( ! empty( $expiry_days ) && is_numeric( $expiry_days ) ) : ?>
            <p style="margin: 0.5rem 0 0; font-size: 0.85rem; color: var(--sw-text-muted);">
                <?php
                echo esc_html( sprintf(
                    /* translators: %d: number of days */
                    __( 'Ważność licencji: %d dni', 'secureware' ),
                    $expiry_days
                ) );
                ?>
            </p>
        <?php else : ?>
            <p style="margin: 0.5rem 0 0; font-size: 0.85rem; color: var(--sw-success);">
                <?php esc_html_e( 'Licencja bezterminowa', 'secureware' ); ?>
            </p>
        <?php endif; ?>
    </div>
    <?php
}
add_action( 'woocommerce_single_product_summary', 'secureware_delivery_info', 25 );

/**
 * Display trust badges on single product page.
 */
function secureware_trust_badges() {
    ?>
    <div class="sw-trust-badges" style="display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--sw-text-muted);">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--sw-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            <?php esc_html_e( '100% oryginalna licencja', 'secureware' ); ?>
        </div>
        <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--sw-text-muted);">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--sw-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <?php esc_html_e( 'Natychmiastowa dostawa', 'secureware' ); ?>
        </div>
        <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--sw-text-muted);">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--sw-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <?php esc_html_e( 'Wsparcie techniczne', 'secureware' ); ?>
        </div>
    </div>
    <?php
}
add_action( 'woocommerce_single_product_summary', 'secureware_trust_badges', 35 );
