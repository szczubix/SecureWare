<?php
/**
 * SecureWare - Content template part
 *
 * @package SecureWare
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>

<article id="post-<?php the_ID(); ?>" <?php post_class( 'sw-product-card' ); ?>>
    <?php if ( has_post_thumbnail() ) : ?>
    <div class="sw-product-card__image">
        <a href="<?php the_permalink(); ?>">
            <?php the_post_thumbnail( 'secureware-product-thumb' ); ?>
        </a>
    </div>
    <?php endif; ?>

    <div class="sw-product-card__body">
        <span class="sw-product-card__category">
            <?php
            $categories = get_the_category();
            if ( ! empty( $categories ) ) {
                echo esc_html( $categories[0]->name );
            }
            ?>
        </span>
        <h3 class="sw-product-card__title">
            <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
        </h3>
        <div class="sw-product-card__meta">
            <span><?php echo esc_html( get_the_date() ); ?></span>
        </div>
        <p><?php echo esc_html( wp_trim_words( get_the_excerpt(), 15 ) ); ?></p>
    </div>
</article>
