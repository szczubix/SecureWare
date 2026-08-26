<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Service;
use SecureWare\Models\SiteContent;

class OfferController
{
    /**
     * Prezentacyjne pogrupowanie usług wg scenariusza (podobnie jak strona
     * "Solutions" u wiodących dostawców backupu) - wyłącznie do wyświetlania
     * na /oferta, nie wpływa na dane w bazie. Usługa spoza mapy trafia do
     * grupy "Pozostałe usługi", więc nowe wpisy dodane w panelu nigdy nie
     * znikają z listy.
     */
    private const GROUPS = [
        'Wdrożenie i zarządzanie' => ['backup-audit', 'backup-implementation', 'managed-backup', 'backup-as-a-service'],
        'Odporność na awarie i ransomware' => ['off-site-backup', 'immutable-backup', 'disaster-recovery', 'restore-testing'],
        'Zakres ochrony' => ['microsoft-365-backup', 'server-backup', 'virtualization-backup'],
        'Nadzór i zgodność' => ['monitoring-24-7', 'retention-compliance'],
    ];

    public function index(Request $request): void
    {
        $services = Service::published();
        $groups   = [];

        foreach (self::GROUPS as $label => $slugs) {
            $groups[$label] = array_values(array_filter($services, fn ($s) => in_array($s['slug'], $slugs, true)));
        }

        $grouped = array_merge(...array_values(self::GROUPS));
        $rest    = array_values(array_filter($services, fn ($s) => !in_array($s['slug'], $grouped, true)));
        if ($rest) {
            $groups['Pozostałe usługi'] = $rest;
        }

        echo View::render('site/offer-index', [
            'groups'          => array_filter($groups),
            'content'         => SiteContent::current()['offer'],
            'metaTitle'       => 'Oferta — SecureWare',
            'metaDescription' => 'Managed Backup, Backup as a Service, Disaster Recovery i inne usługi ochrony danych dla firm.',
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
