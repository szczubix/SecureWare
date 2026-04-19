import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'
import bcrypt from 'bcryptjs'

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL! })
const prisma = new PrismaClient({ adapter })

async function main() {
  console.log('Seed start...')

  const org = await prisma.organization.create({
    data: { name: 'Firma Testowa Sp. z o.o.', plan: 'STANDARD' },
  })

  const hashedPassword = await bcrypt.hash('SecureDesk2026!', 12)

  const user = await prisma.user.create({
    data: {
      email: 'admin@firma.pl',
      name: 'Jan Kowalski',
      password: hashedPassword,
      role: 'OWNER',
      organizationId: org.id,
    },
  })

  await prisma.asset.createMany({
    data: [
      {
        assetNumber: 'AST-001',
        name: 'Baza danych klientów CRM',
        type: 'DATA',
        classification: 'RESTRICTED',
        description: 'Baza danych systemu CRM zawierająca dane osobowe klientów',
        businessOwner: 'Anna Wiśniewska',
        organizationId: org.id,
        nextReviewAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // overdue
      },
      {
        assetNumber: 'AST-002',
        name: 'Kontroler domeny AD-DC01',
        type: 'HARDWARE',
        classification: 'RESTRICTED',
        description: 'Główny kontroler domeny Active Directory',
        location: 'Serwerownia główna',
        technicalOwner: 'Piotr Nowak',
        organizationId: org.id,
        nextReviewAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      },
      {
        assetNumber: 'AST-003',
        name: 'Microsoft 365',
        type: 'CLOUD_SERVICE',
        classification: 'INTERNAL',
        description: 'Pakiet aplikacji biurowych i poczty Microsoft',
        businessOwner: 'Anna Wiśniewska',
        technicalOwner: 'Piotr Nowak',
        organizationId: org.id,
        nextReviewAt: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000),
      },
      {
        assetNumber: 'AST-004',
        name: 'System ERP SAP S/4HANA',
        type: 'SOFTWARE',
        classification: 'CONFIDENTIAL',
        description: 'Główny system ERP do zarządzania procesami biznesowymi',
        location: 'On-premise / DC01',
        organizationId: org.id, // no owner — triggers warning
      },
    ],
  })

  const incident1 = await prisma.incident.create({
    data: {
      incidentNumber: 'INC-2026-001',
      title: 'Podejrzany dostęp do ERP — konto serwisowe',
      description:
        'O godzinie 02:34 Wazuh wygenerował alert o logowaniu konta serwisowego SVC-ERP-SYNC do systemu SAP poza godzinami pracy. Konto nie powinno inicjować sesji interaktywnych. IP źródłowe: 10.0.4.88 (nieznane urządzenie w sieci biurowej).',
      severity: 'CRITICAL',
      status: 'IN_PROGRESS',
      category: 'UNAUTHORIZED_ACCESS',
      reportedBy: 'Jan Kowalski',
      nis2Active: true,
      nis2StartedAt: new Date(Date.now() - 18 * 60 * 60 * 1000), // 18h ago
      organizationId: org.id,
    },
  })

  await prisma.incidentAction.createMany({
    data: [
      {
        incidentId: incident1.id,
        content: 'Incydent zgłoszony i zarejestrowany w systemie.',
        authorId: user.id,
        authorName: 'Jan Kowalski',
      },
      {
        incidentId: incident1.id,
        content:
          'Zablokowano konto SVC-ERP-SYNC w Active Directory. Wyizolowano urządzenie 10.0.4.88 z sieci do czasu wyjaśnienia.',
        authorId: user.id,
        authorName: 'Jan Kowalski',
        createdAt: new Date(Date.now() - 16 * 60 * 60 * 1000),
      },
      {
        incidentId: incident1.id,
        content:
          'Early warning NIS2 przesłany do CERT Polska. Trwa analiza logów systemu SAP za ostatnie 30 dni.',
        authorId: user.id,
        authorName: 'Jan Kowalski',
        createdAt: new Date(Date.now() - 14 * 60 * 60 * 1000),
      },
    ],
  })

  await prisma.incident.create({
    data: {
      incidentNumber: 'INC-2026-002',
      title: 'Phishing — pracownik działu finansów otworzył załącznik',
      description:
        'Pracownik działu finansów otrzymał wiadomość e-mail podszywającą się pod faktury od dostawcy. Wiadomość zawierała złośliwy załącznik .xlsx z makrem. Pracownik otworzył plik, po czym EDR zablokował próbę uruchomienia PowerShell.',
      severity: 'HIGH',
      status: 'ANALYSIS',
      category: 'PHISHING',
      reportedBy: 'Maria Nowak',
      organizationId: org.id,
    },
  })

  await prisma.incident.create({
    data: {
      incidentNumber: 'INC-2026-003',
      title: 'Niedostępność usługi backupu — Veeam',
      description:
        'System backupu Veeam B&R przestał wykonywać zadania o 23:00. Backup nocny nie został ukończony. Przyczyną okazała się pełna przestrzeń dyskowa na repozytorium backupów.',
      severity: 'MEDIUM',
      status: 'CLOSED',
      category: 'AVAILABILITY',
      reportedBy: 'Piotr Nowak',
      closedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
      closureRootCause: 'Wyczerpanie przestrzeni dyskowej na repozytorium backupów (500 GB).',
      closureActions: 'Zwolniono przestrzeń przez usunięcie backupów starszych niż 90 dni. Dodano 2 TB przestrzeni.',
      closurePreventive: 'Wdrożono alert na 80% zapełnienia przestrzeni. Ustalono politykę retencji 60 dni.',
      organizationId: org.id,
    },
  })

  console.log(`Seed zakończony!`)
  console.log(`Email: admin@firma.pl`)
  console.log(`Org ID: ${org.id}`)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(() => prisma.$disconnect())
