<?php
/**
 * SecureWare - WooCommerce Main Template
 *
 * @package SecureWare
 */

get_header();
?>

<div class="sw-content sw-section woocommerce-page">
    <div class="sw-container">
        <?php woocommerce_content(); ?>
    </div>
</div>

<?php get_footer(); ?>
