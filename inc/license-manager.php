<?php
/**
 * SecureWare - License Manager
 *
 * Handles license key generation, storage, delivery, and management.
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Create custom database table for licenses on theme activation.
 */
function secureware_create_license_table() {
    global $wpdb;

    $table_name      = $wpdb->prefix . 'secureware_licenses';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE IF NOT EXISTS $table_name (
        id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
        order_id bigint(20) unsigned NOT NULL,
        product_id bigint(20) unsigned NOT NULL,
        customer_id bigint(20) unsigned NOT NULL,
        license_key varchar(255) NOT NULL,
        status varchar(20) NOT NULL DEFAULT 'active',
        purchase_date datetime NOT NULL,
        expiry_date datetime DEFAULT NULL,
        created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY order_id (order_id),
        KEY customer_id (customer_id),
        KEY license_key (license_key),
        KEY status (status)
    ) $charset_collate;";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta( $sql );
}
add_action( 'after_switch_theme', 'secureware_create_license_table' );

/**
 * Generate a unique license key.
 *
 * @param string $prefix Optional prefix for the key.
 * @return string Generated license key.
 */
function secureware_generate_license_key( $prefix = 'SW' ) {
    $segments = array();
    for ( $i = 0; $i < 4; $i++ ) {
        $segments[] = strtoupper( wp_generate_password( 5, false ) );
    }
    return $prefix . '-' . implode( '-', $segments );
}

/**
 * Assign license keys when an order is completed.
 *
 * @param int $order_id WooCommerce order ID.
 */
function secureware_assign_licenses_on_complete( $order_id ) {
    global $wpdb;

    $order = wc_get_order( $order_id );
    if ( ! $order ) {
        return;
    }

    // Check if licenses already assigned for this order.
    $table_name = $wpdb->prefix . 'secureware_licenses';
    $existing   = $wpdb->get_var(
        $wpdb->prepare( "SELECT COUNT(*) FROM $table_name WHERE order_id = %d", $order_id )
    );

    if ( $existing > 0 ) {
        return;
    }

    $customer_id = $order->get_customer_id();
    $licenses    = array();

    foreach ( $order->get_items() as $item ) {
        $product_id = $item->get_product_id();
        $product    = $item->get_product();
        $quantity   = $item->get_quantity();

        // Check if product has license delivery enabled.
        $is_license_product = get_post_meta( $product_id, '_secureware_is_license', true );
        if ( 'yes' !== $is_license_product ) {
            continue;
        }

        // Check for pre-stored license keys.
        $stored_keys = get_post_meta( $product_id, '_secureware_license_keys', true );
        $stored_keys = ! empty( $stored_keys ) ? array_filter( explode( "\n", $stored_keys ) ) : array();

        // Get expiry days from product meta.
        $expiry_days = get_post_meta( $product_id, '_secureware_license_expiry_days', true );
        $expiry_date = null;
        if ( ! empty( $expiry_days ) && is_numeric( $expiry_days ) ) {
            $expiry_date = gmdate( 'Y-m-d H:i:s', strtotime( "+{$expiry_days} days" ) );
        }

        for ( $i = 0; $i < $quantity; $i++ ) {
            // Use stored key or generate new one.
            if ( ! empty( $stored_keys ) ) {
                $license_key = trim( array_shift( $stored_keys ) );
                // Update remaining keys.
                update_post_meta( $product_id, '_secureware_license_keys', implode( "\n", $stored_keys ) );
            } else {
                $license_key = secureware_generate_license_key();
            }

            // Store in database.
            $wpdb->insert(
                $table_name,
                array(
                    'order_id'      => $order_id,
                    'product_id'    => $product_id,
                    'customer_id'   => $customer_id,
                    'license_key'   => $license_key,
                    'status'        => 'active',
                    'purchase_date' => current_time( 'mysql' ),
                    'expiry_date'   => $expiry_date,
                ),
                array( '%d', '%d', '%d', '%s', '%s', '%s', '%s' )
            );

            $licenses[] = array(
                'product_name' => $product->get_name(),
                'license_key'  => $license_key,
            );
        }
    }

    // Send license delivery email.
    if ( ! empty( $licenses ) ) {
        secureware_send_license_email( $order, $licenses );

        // Store license keys in order meta for reference.
        update_post_meta( $order_id, '_secureware_licenses_delivered', 'yes' );
    }
}
add_action( 'woocommerce_order_status_completed', 'secureware_assign_licenses_on_complete' );

/**
 * Send license delivery email.
 *
 * @param WC_Order $order    WooCommerce order.
 * @param array    $licenses Array of license data.
 */
function secureware_send_license_email( $order, $licenses ) {
    $to      = $order->get_billing_email();
    $subject = sprintf(
        /* translators: %s: order number */
        __( 'Twoje klucze licencyjne - zamówienie #%s', 'secureware' ),
        $order->get_order_number()
    );

    ob_start();
    $email_heading = sprintf(
        /* translators: %s: order number */
        __( 'Klucze licencyjne - zamówienie #%s', 'secureware' ),
        $order->get_order_number()
    );
    $email = null;
    wc_get_template(
        'emails/license-delivery.php',
        array(
            'order'         => $order,
            'licenses'      => $licenses,
            'email_heading' => $email_heading,
            'email'         => $email,
        ),
        '',
        SECUREWARE_DIR . '/woocommerce/'
    );
    $message = ob_get_clean();

    $headers = array( 'Content-Type: text/html; charset=UTF-8' );
    wp_mail( $to, $subject, $message, $headers );
}

/**
 * Get customer licenses for My Account page.
 *
 * @param int $customer_id Customer ID.
 * @return array Array of license data.
 */
function secureware_get_customer_licenses( $customer_id ) {
    global $wpdb;

    $table_name = $wpdb->prefix . 'secureware_licenses';

    $results = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT l.*, p.post_title as product_name
             FROM $table_name l
             LEFT JOIN {$wpdb->posts} p ON l.product_id = p.ID
             WHERE l.customer_id = %d
             ORDER BY l.purchase_date DESC",
            $customer_id
        ),
        ARRAY_A
    );

    $licenses = array();
    if ( $results ) {
        foreach ( $results as $row ) {
            // Check if expired.
            $status = $row['status'];
            if ( 'active' === $status && ! empty( $row['expiry_date'] ) && strtotime( $row['expiry_date'] ) < time() ) {
                $status = 'expired';
                // Update in DB.
                $wpdb->update(
                    $table_name,
                    array( 'status' => 'expired' ),
                    array( 'id' => $row['id'] ),
                    array( '%s' ),
                    array( '%d' )
                );
            }

            $licenses[] = array(
                'product_name'  => $row['product_name'],
                'license_key'   => $row['license_key'],
                'status'        => $status,
                'purchase_date' => wp_date( get_option( 'date_format' ), strtotime( $row['purchase_date'] ) ),
                'expiry_date'   => ! empty( $row['expiry_date'] )
                    ? wp_date( get_option( 'date_format' ), strtotime( $row['expiry_date'] ) )
                    : null,
            );
        }
    }

    return $licenses;
}

/**
 * Add license meta box to WooCommerce product edit screen.
 */
function secureware_add_license_product_fields() {
    global $post;

    echo '<div class="options_group">';

    woocommerce_wp_checkbox( array(
        'id'          => '_secureware_is_license',
        'label'       => __( 'Produkt licencyjny', 'secureware' ),
        'description' => __( 'Zaznacz, jeśli ten produkt to licencja na oprogramowanie.', 'secureware' ),
    ) );

    woocommerce_wp_text_input( array(
        'id'          => '_secureware_license_expiry_days',
        'label'       => __( 'Ważność licencji (dni)', 'secureware' ),
        'description' => __( 'Pozostaw puste dla licencji bezterminowej.', 'secureware' ),
        'type'        => 'number',
        'desc_tip'    => true,
    ) );

    woocommerce_wp_textarea_input( array(
        'id'          => '_secureware_license_keys',
        'label'       => __( 'Klucze licencyjne', 'secureware' ),
        'description' => __( 'Wpisz klucze licencyjne, każdy w nowej linii. Klucze będą wydawane po kolei. Gdy się skończą, system wygeneruje je automatycznie.', 'secureware' ),
        'desc_tip'    => true,
        'rows'        => 5,
    ) );

    echo '</div>';
}
add_action( 'woocommerce_product_options_general_product_data', 'secureware_add_license_product_fields' );

/**
 * Save license product fields.
 *
 * @param int $post_id Product post ID.
 */
function secureware_save_license_product_fields( $post_id ) {
    $is_license = isset( $_POST['_secureware_is_license'] ) ? 'yes' : 'no';
    update_post_meta( $post_id, '_secureware_is_license', sanitize_text_field( $is_license ) );

    if ( isset( $_POST['_secureware_license_expiry_days'] ) ) {
        update_post_meta( $post_id, '_secureware_license_expiry_days', absint( $_POST['_secureware_license_expiry_days'] ) );
    }

    if ( isset( $_POST['_secureware_license_keys'] ) ) {
        update_post_meta( $post_id, '_secureware_license_keys', sanitize_textarea_field( $_POST['_secureware_license_keys'] ) );
    }
}
add_action( 'woocommerce_process_product_meta', 'secureware_save_license_product_fields' );

/**
 * Display license keys on order detail page (admin).
 *
 * @param WC_Order $order WooCommerce order.
 */
function secureware_display_order_licenses( $order ) {
    global $wpdb;

    $table_name = $wpdb->prefix . 'secureware_licenses';
    $licenses   = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT l.*, p.post_title as product_name
             FROM $table_name l
             LEFT JOIN {$wpdb->posts} p ON l.product_id = p.ID
             WHERE l.order_id = %d",
            $order->get_id()
        )
    );

    if ( empty( $licenses ) ) {
        return;
    }
    ?>
    <h3><?php esc_html_e( 'Klucze licencyjne', 'secureware' ); ?></h3>
    <table class="widefat striped">
        <thead>
            <tr>
                <th><?php esc_html_e( 'Produkt', 'secureware' ); ?></th>
                <th><?php esc_html_e( 'Klucz', 'secureware' ); ?></th>
                <th><?php esc_html_e( 'Status', 'secureware' ); ?></th>
                <th><?php esc_html_e( 'Wygasa', 'secureware' ); ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ( $licenses as $license ) : ?>
                <tr>
                    <td><?php echo esc_html( $license->product_name ); ?></td>
                    <td><code><?php echo esc_html( $license->license_key ); ?></code></td>
                    <td><?php echo esc_html( $license->status ); ?></td>
                    <td><?php echo $license->expiry_date ? esc_html( wp_date( get_option( 'date_format' ), strtotime( $license->expiry_date ) ) ) : esc_html__( 'Bezterminowa', 'secureware' ); ?></td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php
}
add_action( 'woocommerce_admin_order_data_after_order_details', 'secureware_display_order_licenses' );

/**
 * Show license keys on thank-you page.
 *
 * @param int $order_id Order ID.
 */
function secureware_thankyou_license_display( $order_id ) {
    global $wpdb;

    $table_name = $wpdb->prefix . 'secureware_licenses';
    $licenses   = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT l.*, p.post_title as product_name
             FROM $table_name l
             LEFT JOIN {$wpdb->posts} p ON l.product_id = p.ID
             WHERE l.order_id = %d",
            $order_id
        )
    );

    if ( empty( $licenses ) ) {
        return;
    }
    ?>
    <section class="sw-thankyou-licenses">
        <h2><?php esc_html_e( 'Twoje klucze licencyjne', 'secureware' ); ?></h2>
        <p><?php esc_html_e( 'Poniżej znajdziesz klucze do zakupionych produktów. Klucze zostały również wysłane na Twój adres e-mail.', 'secureware' ); ?></p>
        <?php foreach ( $licenses as $license ) : ?>
        <div style="margin-bottom: 1rem;">
            <strong><?php echo esc_html( $license->product_name ); ?></strong>
            <div class="sw-license-key">
                <code class="sw-license-key__value"><?php echo esc_html( $license->license_key ); ?></code>
                <button class="sw-license-key__copy" data-key="<?php echo esc_attr( $license->license_key ); ?>">
                    <?php esc_html_e( 'Kopiuj', 'secureware' ); ?>
                </button>
            </div>
        </div>
        <?php endforeach; ?>
    </section>
    <?php
}
add_action( 'woocommerce_thankyou', 'secureware_thankyou_license_display', 20 );
