<?php
/**
 * SecureWare - No content template
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>

<div class="sw-no-results" style="text-align: center; padding: 4rem 1.5rem;">
    <h2><?php esc_html_e( 'Brak wyników', 'secureware' ); ?></h2>
    <p style="color: var(--sw-text-muted); max-width: 500px; margin: 1rem auto;">
        <?php if ( is_search() ) : ?>
            <?php esc_html_e( 'Nie znaleziono wyników dla tego wyszukiwania. Spróbuj użyć innych słów kluczowych.', 'secureware' ); ?>
        <?php else : ?>
            <?php esc_html_e( 'Wygląda na to, że nie ma tu jeszcze żadnej treści.', 'secureware' ); ?>
        <?php endif; ?>
    </p>
    <?php if ( is_search() ) : ?>
        <?php get_search_form(); ?>
    <?php endif; ?>
</div>
