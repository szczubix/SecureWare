<?php
/**
 * SecureWare - License Delivery Email Template
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/*
 * @hooked WC_Emails::email_header() Output the email header
 */
do_action( 'woocommerce_email_header', $email_heading, $email );
?>

<p><?php
echo esc_html( sprintf(
    /* translators: %s: customer first name */
    __( 'Cześć %s,', 'secureware' ),
    $order->get_billing_first_name()
) );
?></p>

<p><?php esc_html_e( 'Dziękujemy za zakup! Oto Twoje klucze licencyjne:', 'secureware' ); ?></p>

<?php if ( ! empty( $licenses ) ) : ?>
<table cellspacing="0" cellpadding="10" style="width: 100%; border-collapse: collapse; margin: 20px 0;">
    <thead>
        <tr>
            <th style="background: #1a2035; color: #e2e8f0; padding: 12px 15px; text-align: left; border-bottom: 2px solid #00d4ff;"><?php esc_html_e( 'Produkt', 'secureware' ); ?></th>
            <th style="background: #1a2035; color: #e2e8f0; padding: 12px 15px; text-align: left; border-bottom: 2px solid #00d4ff;"><?php esc_html_e( 'Klucz licencyjny', 'secureware' ); ?></th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ( $licenses as $license ) : ?>
        <tr>
            <td style="padding: 12px 15px; border-bottom: 1px solid #2a3555; color: #94a3b8;">
                <?php echo esc_html( $license['product_name'] ); ?>
            </td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #2a3555;">
                <code style="font-family: 'JetBrains Mono', monospace; color: #00d4ff; font-size: 14px; background: #0a0e17; padding: 4px 8px; border-radius: 4px;">
                    <?php echo esc_html( $license['license_key'] ); ?>
                </code>
            </td>
        </tr>
        <?php endforeach; ?>
    </tbody>
</table>
<?php endif; ?>

<p><?php esc_html_e( 'Klucze licencyjne są również dostępne w Twoim panelu klienta w zakładce "Moje licencje".', 'secureware' ); ?></p>

<p><?php esc_html_e( 'Jeśli potrzebujesz pomocy z instalacją lub aktywacją, skontaktuj się z naszym działem wsparcia.', 'secureware' ); ?></p>

<?php
/*
 * @hooked WC_Emails::email_footer() Output the email footer
 */
do_action( 'woocommerce_email_footer', $email );
?>
