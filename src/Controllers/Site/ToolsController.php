<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Core\Request;
use SecureWare\Core\View;

class ToolsController
{
    public function downtimeCalculator(Request $request): void
    {
        echo View::render('site/downtime-calculator', [
            'metaTitle'       => Lang::t('calc.meta_title'),
            'metaDescription' => Lang::t('calc.meta_description'),
        ], 'site/layout');
    }
}
