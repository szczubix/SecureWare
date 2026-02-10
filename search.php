<?php
/**
 * SecureWare - Search Results Template
 *
 * @package SecureWare
 */

get_header();
?>

<div class="sw-content sw-section">
    <div class="sw-container">
        <header class="sw-archive__header">
            <h1 class="sw-archive__title">
                <?php
                echo esc_html( sprintf(
                    /* translators: %s: search query */
                    __( 'Wyniki wyszukiwania: "%s"', 'secureware' ),
                    get_search_query()
                ) );
                ?>
            </h1>
        </header>

        <?php if ( have_posts() ) : ?>
            <div class="sw-grid sw-grid-3">
                <?php while ( have_posts() ) : the_post(); ?>
                    <?php get_template_part( 'template-parts/content', get_post_type() ); ?>
                <?php endwhile; ?>
            </div>

            <?php the_posts_pagination( array(
                'mid_size'  => 2,
                'prev_text' => '&larr;',
                'next_text' => '&rarr;',
            ) ); ?>
        <?php else : ?>
            <?php get_template_part( 'template-parts/content', 'none' ); ?>
        <?php endif; ?>
    </div>
</div>

<?php get_footer(); ?>
