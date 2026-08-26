<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
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
     * znikają z listy. Klucze grup sa stabilne (nie tlumaczone) - etykiety
     * do wyswietlenia pochodza z Lang::t(), zeby dzialaly w obu jezykach.
     */
    private const GROUPS = [
        'deployment' => ['backup-audit', 'backup-implementation', 'managed-backup', 'backup-as-a-service'],
        'resilience' => ['off-site-backup', 'immutable-backup', 'disaster-recovery', 'restore-testing'],
        'scope'      => ['microsoft-365-backup', 'server-backup', 'virtualization-backup'],
        'governance' => ['monitoring-24-7', 'retention-compliance'],
    ];

    public function index(Request $request): void
    {
        $services = Service::published(Locale::current());
        $groups   = [];

        foreach (self::GROUPS as $key => $slugs) {
            $groups[Lang::t('offer.group.' . $key)] = array_values(array_filter($services, fn ($s) => in_array($s['slug'], $slugs, true)));
        }

        $grouped = array_merge(...array_values(self::GROUPS));
        $rest    = array_values(array_filter($services, fn ($s) => !in_array($s['slug'], $grouped, true)));
        if ($rest) {
            $groups[Lang::t('offer.group.other')] = $rest;
        }

        echo View::render('site/offer-index', [
            'groups'          => array_filter($groups),
            'content'         => SiteContent::current(Locale::current())['offer'],
            'metaTitle'       => Lang::t('offer.meta_title'),
            'metaDescription' => Lang::t('offer.meta_description'),
        ], 'site/layout');
    }

    public function show(Request $request, string $slug): void
    {
        $service = Service::findBySlug($slug, Locale::current());
        if (!$service) {
            Response::notFound();
        }

        echo View::render('site/offer-single', [
            'service'         => $service,
            'otherServices'   => array_values(array_filter(Service::published(Locale::current()), fn ($s) => $s['id'] !== $service['id'])),
            'metaTitle'       => $service['meta_title'] ?: ($service['name'] . ' — SecureWare'),
            'metaDescription' => $service['meta_description'] ?: $service['short_description'],
        ], 'site/layout');
    }
}
