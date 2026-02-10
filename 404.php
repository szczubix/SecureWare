<?php
/**
 * SecureWare - 404 Template
 *
 * @package SecureWare
 */

get_header();
?>

<div class="sw-content sw-section">
    <div class="sw-container" style="text-align: center; padding: 6rem 1.5rem;">
        <div style="font-size: 6rem; font-weight: 800; background: var(--sw-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 1rem;">404</div>
        <h1><?php esc_html_e( 'Strona nie znaleziona', 'secureware' ); ?></h1>
        <p style="max-width: 500px; margin: 1rem auto 2rem; color: var(--sw-text-muted);">
            <?php esc_html_e( 'Przepraszamy, strona której szukasz nie istnieje lub została przeniesiona.', 'secureware' ); ?>
        </p>
        <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="sw-btn sw-btn--primary">
            <?php esc_html_e( 'Wróć do strony głównej', 'secureware' ); ?>
        </a>
    </div>
</div>

<?php get_footer(); ?>
