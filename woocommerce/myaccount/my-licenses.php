<?php
/**
 * SecureWare - My Licenses page (My Account)
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

$customer_id = get_current_user_id();
$licenses    = secureware_get_customer_licenses( $customer_id );
?>

<div class="sw-my-licenses">
    <h2><?php esc_html_e( 'Moje licencje', 'secureware' ); ?></h2>

    <?php if ( ! empty( $licenses ) ) : ?>
        <table class="sw-licenses-table">
            <thead>
                <tr>
                    <th><?php esc_html_e( 'Produkt', 'secureware' ); ?></th>
                    <th><?php esc_html_e( 'Klucz licencyjny', 'secureware' ); ?></th>
                    <th><?php esc_html_e( 'Status', 'secureware' ); ?></th>
                    <th><?php esc_html_e( 'Data zakupu', 'secureware' ); ?></th>
                    <th><?php esc_html_e( 'Wygasa', 'secureware' ); ?></th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ( $licenses as $license ) : ?>
                    <tr>
                        <td>
                            <strong><?php echo esc_html( $license['product_name'] ); ?></strong>
                        </td>
                        <td>
                            <div class="sw-license-key">
                                <code class="sw-license-key__value"><?php echo esc_html( $license['license_key'] ); ?></code>
                                <button class="sw-license-key__copy" data-key="<?php echo esc_attr( $license['license_key'] ); ?>">
                                    <?php esc_html_e( 'Kopiuj', 'secureware' ); ?>
                                </button>
                            </div>
                        </td>
                        <td>
                            <?php
                            $status_class = 'sw-status--' . esc_attr( $license['status'] );
                            $status_labels = array(
                                'active'  => __( 'Aktywna', 'secureware' ),
                                'expired' => __( 'Wygasła', 'secureware' ),
                                'pending' => __( 'Oczekująca', 'secureware' ),
                            );
                            $status_label = isset( $status_labels[ $license['status'] ] ) ? $status_labels[ $license['status'] ] : $license['status'];
                            ?>
                            <span class="sw-status <?php echo esc_attr( $status_class ); ?>">
                                <?php echo esc_html( $status_label ); ?>
                            </span>
                        </td>
                        <td><?php echo esc_html( $license['purchase_date'] ); ?></td>
                        <td>
                            <?php
                            echo $license['expiry_date']
                                ? esc_html( $license['expiry_date'] )
                                : esc_html__( 'Bezterminowa', 'secureware' );
                            ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php else : ?>
        <div class="woocommerce-info">
            <?php esc_html_e( 'Nie masz jeszcze żadnych licencji. Odwiedź nasz sklep, aby dokonać pierwszego zakupu!', 'secureware' ); ?>
        </div>
        <a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>" class="sw-btn sw-btn--primary">
            <?php esc_html_e( 'Przeglądaj sklep', 'secureware' ); ?>
        </a>
    <?php endif; ?>
</div>
