<?php
/**
 * SecureWare - Single Post Template
 *
 * @package SecureWare
 */

get_header();
?>

<div class="sw-content sw-section">
    <div class="sw-container">
        <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class( 'sw-single' ); ?>>
                <header class="sw-single__header">
                    <h1 class="sw-single__title"><?php the_title(); ?></h1>
                    <div class="sw-single__meta">
                        <span><?php echo esc_html( get_the_date() ); ?></span>
                        <span><?php the_author(); ?></span>
                    </div>
                </header>
                <?php if ( has_post_thumbnail() ) : ?>
                    <div class="sw-single__thumbnail">
                        <?php the_post_thumbnail( 'large' ); ?>
                    </div>
                <?php endif; ?>
                <div class="sw-single__content">
                    <?php the_content(); ?>
                </div>
            </article>
        <?php endwhile; ?>
    </div>
</div>

<?php get_footer(); ?>
