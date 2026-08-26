<?php

/**
 * Angielskie tlumaczenia domyslnej tresci (uslugi/podstrony CMS/artykuly/
 * kategoria) zdefiniowanej w services.php/pages.php/articles.php - klucze
 * to slugi, po ktorych Installer::seedTranslations() dopasowuje wpisy w
 * bazie (nie tworzy nowych wierszy, tylko tlumaczenia dla istniejacych).
 * Uzywane zarowno przy pierwszej instalacji jak i przez refresh-content.php
 * na juz dzialajacej instalacji.
 */
return [
    'services' => [
        'managed-backup' => [
            'name' => 'Managed Backup',
            'short_description' => 'We take over full management of your existing backup environment - Veeam, Proxmox Backup Server, and others - so you don\'t have to watch it yourself.',
            'content' => '<p>Already have backup in place, but no time or in-house expertise to keep watching it? Managed Backup means we take over day-to-day oversight of your existing environment - whether it runs on Veeam, Proxmox Backup Server, or another platform.</p><ul><li>Daily verification of backup jobs and repositories</li><li>Responding to errors and alerts before they become a problem</li><li>Optimizing retention policies and performance</li><li>Monthly data protection status report</li></ul><p>The result: backup that just works, while you get a clear report instead of stress.</p>',
        ],
        'backup-as-a-service' => [
            'name' => 'Backup as a Service',
            'short_description' => 'We install an agent in your environment and your backups land securely on our infrastructure - no investment in your own hardware required.',
            'content' => '<p>Backup as a Service (BaaS) is the fastest route to professional data protection without building your own backup infrastructure. We deploy a lightweight agent in your environment, and data travels over an encrypted channel to our infrastructure.</p><ul><li>Zero hardware or licensing investment on your side</li><li>Capacity scales as you need it</li><li>Data encrypted in transit and at rest</li><li>Simple subscription-based billing</li></ul><p>An ideal fit for companies that want backup "ready to go", without a months-long deployment.</p>',
        ],
        'off-site-backup' => [
            'name' => 'Off-site Backup',
            'short_description' => 'A second backup copy stored physically away from the client\'s premises - protection against fire, theft, and local infrastructure failure.',
            'content' => '<p>The 3-2-1 rule is clear: at least one copy of your data should live off-site. Off-site Backup delivers exactly that - your data is replicated to an independent location, fully separated from your server room.</p><ul><li>Protection against fire, flooding, theft of equipment</li><li>An independent geographic location</li><li>Automatic, recurring replication</li><li>Fast restore from the backup location if needed</li></ul>',
        ],
        'immutable-backup' => [
            'name' => 'Immutable Backup',
            'short_description' => 'A backup repository protected against modification and deletion - real protection against ransomware, even if an attacker gains administrator access.',
            'content' => '<p>Modern ransomware targets backup copies too. Immutable Backup stores data in a repository that cannot be overwritten or deleted for a defined period - not even with administrator privileges.</p><ul><li>Data immutability throughout the retention window</li><li>Protection against ransomware and insider threats</li><li>Compliant with audit and regulatory requirements</li><li>Works with Veeam, PBS, and other backup platforms</li></ul><p>This is the last line of defense when every other safeguard fails.</p>',
        ],
        'microsoft-365-backup' => [
            'name' => 'Microsoft 365 Backup',
            'short_description' => 'Backups for Exchange Online, OneDrive, SharePoint, and Teams - because Microsoft is responsible for service availability, not for recovering your data.',
            'content' => '<p>Many companies assume data in Microsoft 365 is "safe in the cloud". In reality, Microsoft is responsible for infrastructure availability - not for accidental deletion, user error, or a mailbox attack.</p><ul><li>Backup for Exchange Online (mail, calendars, contacts)</li><li>Backup for OneDrive and SharePoint</li><li>Backup for Microsoft Teams teams and channels</li><li>Fast recovery of individual items or entire mailboxes</li></ul>',
        ],
        'server-backup' => [
            'name' => 'Server Backup',
            'short_description' => 'Backups for physical Windows and Linux servers - full system images as well as file- and application-level backup.',
            'content' => '<p>We provide comprehensive protection for physical servers running Windows Server and Linux - from full bare-metal system images to file- and application-level backup (databases, domain controllers, mail servers).</p><ul><li>Full system backup (bare-metal restore)</li><li>Application-aware backup with data consistency (VSS)</li><li>Support for Windows Server and major Linux distributions</li><li>Flexible schedules and retention policies</li></ul>',
        ],
        'virtualization-backup' => [
            'name' => 'Virtualization Backup',
            'short_description' => 'Backup for virtualized environments - VMware vSphere, Microsoft Hyper-V, and Proxmox VE - with no agent installed inside every machine.',
            'content' => '<p>Virtualized environments need a different approach to backup than individual servers. We provide hypervisor-level backup for VMware vSphere, Microsoft Hyper-V, and Proxmox VE, with no need to install an agent inside every virtual machine.</p><ul><li>Hypervisor-level (image-based) backup</li><li>Support for VMware, Hyper-V, and Proxmox VE</li><li>Fast recovery of entire virtual machines</li><li>Minimal load on the production environment</li></ul>',
        ],
        'disaster-recovery' => [
            'name' => 'Disaster Recovery',
            'short_description' => 'Recovery procedures and infrastructure for a major outage - from a DR plan to a standby environment you can bring up in minutes.',
            'content' => '<p>Backup is not the same as Disaster Recovery. Backup lets you recover data - DR lets you recover your business operations. We design and maintain recovery procedures and infrastructure matched to your RTO and RPO targets.</p><ul><li>Developing a Disaster Recovery Plan (DRP)</li><li>A standby environment ready for a fast failover</li><li>Defining and monitoring RTO/RPO</li><li>Regular tests of failure scenarios</li></ul>',
        ],
        'restore-testing' => [
            'name' => 'Restore Testing',
            'short_description' => 'Recurring, real data restore tests - because a backup that\'s never been checked is just an assumption, not a safeguard.',
            'content' => '<p>The most common reason backup fails at the critical moment is a lack of restore testing. We regularly perform real data restore tests - not just a check of the backup job\'s status.</p><ul><li>A schedule of recurring restore tests</li><li>Testing in an isolated (sandbox) environment</li><li>A report with recommendations after every test</li><li>Verification of data consistency and completeness</li></ul>',
        ],
        'backup-audit' => [
            'name' => 'Backup Audit',
            'short_description' => 'An independent review of the client\'s current backup environment - we identify gaps and risks and recommend concrete fixes.',
            'content' => '<p>Before you start changing anything, it\'s worth knowing where you actually stand. Backup Audit is an independent review of your current data protection environment - configuration, retention policies, coverage, and real resilience to failure.</p><ul><li>Review of backup configuration and policies</li><li>Identifying coverage gaps (unprotected systems)</li><li>Assessing compliance with the 3-2-1 rule</li><li>A report with prioritized recommendations</li></ul>',
        ],
        'backup-implementation' => [
            'name' => 'Backup Implementation',
            'short_description' => 'We design and deploy a backup environment from scratch - from choosing the architecture to full go-live and documentation handover.',
            'content' => '<p>When a company doesn\'t yet have organized backup, or the current solution needs replacing, we design and deploy an environment from the ground up - matched to your scale, budget, and security requirements.</p><ul><li>Needs analysis and backup architecture selection</li><li>Deployment and configuration of the chosen platform</li><li>Migration from an existing solution (if applicable)</li><li>Post-deployment documentation and team training</li></ul>',
        ],
        'monitoring-24-7' => [
            'name' => '24/7 Monitoring',
            'short_description' => 'Round-the-clock oversight of backup jobs, repositories, and capacity - alerts reach us before they become your problem.',
            'content' => '<p>Backup that nobody monitors will sooner or later fail quietly - one failed job that nobody notices can cost you your data. Our team monitors your backup environment 24 hours a day, 7 days a week.</p><ul><li>Round-the-clock monitoring of backup jobs</li><li>Alerts for errors and repository capacity thresholds</li><li>Proactive response to incidents</li><li>A status dashboard available to the client</li></ul>',
        ],
        'retention-compliance' => [
            'name' => 'Retention & Compliance',
            'short_description' => 'Data retention policies, reporting, and documentation aligned with audit requirements and industry regulations.',
            'content' => '<p>Proper data retention isn\'t just a technical matter - it\'s also about regulatory and audit compliance. We help design and maintain retention policies that meet legal and industry requirements.</p><ul><li>Designing retention policies matched to your requirements</li><li>Compliance reporting for audits</li><li>Documentation of data protection processes</li><li>Support during external audits</li></ul>',
        ],
    ],
    'pages' => [
        'o-nas' => [
            'title' => 'About us',
            'meta_description' => 'SecureWare - a team of specialists in backup, disaster recovery, and data protection for businesses.',
            'content' => '<h2>Who we are</h2><p>SecureWare is a team of specialists focused on a single area: data protection. Managed backup, backup as a service, disaster recovery, and recurring restore tests - that\'s everything we do, and we do it well.</p><h2>How we work</h2><p>We don\'t sell a one-off deployment and disappear. Every environment we look after is monitored 24/7, regularly tested, and reported on in a way that makes sense - even outside of IT.</p><h2>Who we work with</h2><p>We work with companies for whom losing data means real financial and reputational damage - and who want certainty that, in the event of an outage, their data will come back, not just "probably come back".</p>',
        ],
        'polityka-prywatnosci' => [
            'title' => 'Privacy Policy',
            'meta_description' => 'Information about the processing of personal data by SecureWare.',
            'content' => '<h2>Data controller</h2><p>The controller of personal data processed in connection with the use of the secureware.pl website is SecureWare. The controller\'s contact details can be found in the site footer and on the Contact page.</p><h2>What data we process</h2><p>We process data provided voluntarily via the contact form (name, email address, phone number, message content) in order to respond to your inquiry and prepare a quote.</p><h2>Cookies</h2><p>The website uses cookies for statistical purposes (Google Analytics) and to manage data processing consent (CookieYes). You can change your detailed consent settings at any time from the cookie banner.</p><h2>Your rights</h2><p>You have the right to access, correct, delete, and restrict the processing of your data. To exercise your rights, please contact us via the contact form.</p><p><em>This content is a template and should be reviewed by a lawyer before production use.</em></p>',
        ],
        'regulamin' => [
            'title' => 'Terms of Service',
            'meta_description' => 'Terms of use for the secureware.pl website and terms of service provided by SecureWare.',
            'content' => '<h2>General provisions</h2><p>These terms set out the rules for using the secureware.pl website and the general terms for backup, disaster recovery, and related services provided by SecureWare.</p><h2>Scope of services</h2><p>The detailed scope, terms, and pricing of individual services (Managed Backup, Backup as a Service, Disaster Recovery, and others) are set out on a case-by-case basis in an individual agreement or commercial offer.</p><h2>Complaints</h2><p>Complaints regarding the services provided can be submitted via the contact form or the email address listed in the website footer.</p><p><em>This content is a template and should be reviewed by a lawyer before production use.</em></p>',
        ],
    ],
    'articles' => [
        'zasada-3-2-1-backupu' => [
            'title' => 'The 3-2-1 backup rule - why one copy is never enough',
            'excerpt' => 'Three copies of data, two different media, one copy off-site - how to put the classic backup rule into practice, the one that still saves companies from data loss.',
            'content' => '<p>The 3-2-1 rule is one of the oldest, and still one of the most effective, foundations of a backup strategy. It says: keep at least <strong>3 copies</strong> of your data, on <strong>2 different types of media</strong>, with <strong>1 copy</strong> stored off-site.</p><h2>Why one copy is not enough</h2><p>Companies often assume that if data is "backed up somewhere", it\'s safe. In practice, a single backup copy stored in the same server room as the production data is exposed to the same risks: fire, flooding, theft of equipment, or a ransomware attack that encrypts everything within reach on the network.</p><h2>What this looks like in practice</h2><ul><li>The production copy (live data)</li><li>A local copy on a separate medium/repository</li><li>An off-site copy, or one in the cloud</li></ul><p>Increasingly, a "1 immutable" rule is added too - a copy that cannot be deleted or encrypted, even with administrator privileges.</p>',
        ],
        'ransomware-atakuje-backupy' => [
            'title' => 'Ransomware targets backups too - how to defend against it',
            'excerpt' => 'Modern ransomware attacks increasingly target backup repositories directly. Find out which mechanisms actually protect your backups from encryption.',
            'content' => '<p>For years, backup was treated as the last line of defense against ransomware - if production data got encrypted, you simply restored it from a backup copy. Modern attacks have changed that rulebook.</p><h2>The attackers\' new playbook</h2><p>Advanced ransomware groups spend weeks inside a victim\'s network first, identifying the backup infrastructure, and only then trigger encryption - covering the backup repositories and management consoles as well.</p><h2>What actually works</h2><ul><li>Immutable copies - data cannot be overwritten or deleted within the retention window</li><li>Separate, restricted access accounts for the backup system</li><li>Network segmentation between production and backup infrastructure</li><li>Regular, real restore tests</li></ul><p>Backup without these mechanisms is, at best, an extra delay for the attacker - not real protection.</p>',
        ],
        'rto-i-rpo-wyjasnione' => [
            'title' => 'RTO and RPO - two numbers that decide whether your company survives an outage',
            'excerpt' => 'Recovery Time Objective and Recovery Point Objective are the core metrics of every disaster recovery plan. We explain what they mean and how to set them for your business.',
            'content' => '<p>Every disaster recovery strategy rests on two key parameters: RTO and RPO. Understanding the difference between them is the first step to designing a recovery plan that actually matches your business needs.</p><h2>RTO - Recovery Time Objective</h2><p>The maximum acceptable time within which a system must be restored to operation after an outage. If your RTO is 4 hours, that means key systems must be back up 4 hours after the outage occurred.</p><h2>RPO - Recovery Point Objective</h2><p>The maximum acceptable amount of data a company can lose, measured as time since the last backup. An RPO of 1 hour means that, in the worst case, you\'ll lose data from the last hour before the outage.</p><h2>How to set the right values</h2><p>Not every system in a company needs the same level of protection. A sales system might need an RTO measured in minutes, while a document archive might tolerate an RTO measured in days. Matching RTO/RPO to a system\'s real business value lets you optimize protection costs.</p>',
        ],
    ],
    'categories' => [
        'backup-i-bezpieczenstwo' => [
            'name' => 'Backup & Security',
        ],
    ],
    // Ustawienia jednowartosciowe (nie sa per-encja, wiec nie ida przez
    // tabele translations - osobne klucze "*_en" w settings).
    'settings' => [
        'site_tagline_en' => 'Backup and disaster recovery that work when you need them most.',
        'footer_text_en'  => '© %YEAR% SecureWare. All rights reserved.',
        'nav_menu_en' => [
            ['label' => 'Services', 'url' => '/oferta'],
            ['label' => 'Blog', 'url' => '/blog'],
            ['label' => 'About us', 'url' => '/o-nas'],
            ['label' => 'Contact', 'url' => '/kontakt'],
        ],
    ],
];
