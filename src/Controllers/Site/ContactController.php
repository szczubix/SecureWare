<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Csrf;
use SecureWare\Core\Request;
use SecureWare\Core\View;
use SecureWare\Models\Lead;
use SecureWare\Models\Setting;

class ContactController
{
    public function show(Request $request): void
    {
        echo View::render('site/contact', [
            'success'         => false,
            'error'           => null,
            'old'             => [],
            'turnstileSiteKey'=> Setting::get('turnstile_site_key', ''),
            'metaTitle'       => 'Kontakt — SecureWare',
            'metaDescription' => 'Skontaktuj sie z nami - wycena backupu, disaster recovery i ochrony danych dla Twojej firmy.',
        ], 'site/layout');
    }

    public function submit(Request $request): void
    {
        $old = [
            'name'    => (string) $request->input('name', ''),
            'company' => (string) $request->input('company', ''),
            'email'   => (string) $request->input('email', ''),
            'phone'   => (string) $request->input('phone', ''),
            'message' => (string) $request->input('message', ''),
        ];

        $render = function (string $error) use ($old) {
            echo View::render('site/contact', [
                'success' => false,
                'error'   => $error,
                'old'     => $old,
                'turnstileSiteKey' => Setting::get('turnstile_site_key', ''),
                'metaTitle'        => 'Kontakt — SecureWare',
                'metaDescription'  => '',
            ], 'site/layout');
        };

        if (!Csrf::verify($request->input('_csrf'))) {
            $render('Sesja wygasla. Odswiez strone i sprobuj ponownie.');
            return;
        }

        if ($old['name'] === '' || !filter_var($old['email'], FILTER_VALIDATE_EMAIL) || $old['message'] === '') {
            $render('Wypelnij imie, poprawny adres e-mail oraz wiadomosc.');
            return;
        }

        $secret = Setting::get('turnstile_secret', '');
        if ($secret) {
            $token = (string) $request->input('cf-turnstile-response', '');
            if (!$this->verifyTurnstile($secret, $token, $request->ip())) {
                $render('Weryfikacja antyspamowa nie powiodla sie. Sprobuj ponownie.');
                return;
            }
        }

        Lead::create($old['name'], $old['email'], $old['phone'] ?: null, $old['company'] ?: null, $old['message'], '/kontakt');
        $this->notify($old);

        echo View::render('site/contact', [
            'success' => true,
            'error'   => null,
            'old'     => [],
            'turnstileSiteKey' => Setting::get('turnstile_site_key', ''),
            'metaTitle'        => 'Kontakt — SecureWare',
            'metaDescription'  => '',
        ], 'site/layout');
    }

    private function verifyTurnstile(string $secret, string $token, string $ip): bool
    {
        if ($token === '') {
            return false;
        }

        $ch = curl_init('https://challenges.cloudflare.com/turnstile/v0/siteverify');
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => http_build_query(['secret' => $secret, 'response' => $token, 'remoteip' => $ip]),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 8,
        ]);
        $response = curl_exec($ch);
        curl_close($ch);

        if ($response === false) {
            return false;
        }

        $data = json_decode($response, true);
        return !empty($data['success']);
    }

    private function notify(array $lead): void
    {
        $to = Setting::get('contact_email', '');
        if (!$to) {
            return;
        }

        $subject = 'Nowe zapytanie ze strony SecureWare';
        $body    = "Imie: {$lead['name']}\nFirma: {$lead['company']}\nE-mail: {$lead['email']}\nTelefon: {$lead['phone']}\n\nWiadomosc:\n{$lead['message']}";
        $headers = 'From: no-reply@secureware.pl' . "\r\n" . 'Reply-To: ' . $lead['email'];

        @mail($to, $subject, $body, $headers);
    }
}
