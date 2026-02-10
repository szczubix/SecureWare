<?php
/**
 * SecureWare - Sidebar Template
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

if ( ! is_active_sidebar( 'shop-sidebar' ) ) {
    return;
}
?>

<aside id="secondary" class="sw-sidebar" role="complementary">
    <?php dynamic_sidebar( 'shop-sidebar' ); ?>
</aside>
