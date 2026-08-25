<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Service;

class OfferController
{
    public function index(Request $request): void
    {
        echo View::render('site/offer-index', [
            'services'        => Service::published(),
            'metaTitle'       => 'Oferta — SecureWare',
            'metaDescription' => 'Managed Backup, Backup as a Service, Disaster Recovery i inne uslugi ochrony danych dla firm.',
        ], 'site/layout');
    }

    public function show(Request $request, string $slug): void
    {
        $service = Service::findBySlug($slug);
        if (!$service) {
            Response::notFound();
        }

        echo View::render('site/offer-single', [
            'service'         => $service,
            'otherServices'   => array_values(array_filter(Service::published(), fn ($s) => $s['id'] !== $service['id'])),
            'metaTitle'       => $service['meta_title'] ?: ($service['name'] . ' — SecureWare'),
            'metaDescription' => $service['meta_description'] ?: $service['short_description'],
        ], 'site/layout');
    }
}
