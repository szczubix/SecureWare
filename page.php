<?php
/**
 * SecureWare - Page Template
 *
 * @package SecureWare
 */

get_header();
?>

<div class="sw-content sw-section">
    <div class="sw-container">
        <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class( 'sw-page' ); ?>>
                <header class="sw-page__header">
                    <h1 class="sw-page__title"><?php the_title(); ?></h1>
                </header>
                <div class="sw-page__content">
                    <?php the_content(); ?>
                </div>
            </article>
        <?php endwhile; ?>
    </div>
</div>

<?php get_footer(); ?>
