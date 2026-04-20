import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { redirect, notFound } from 'next/navigation'

const SEVERITY_PL: Record<string, string> = { CRITICAL: 'Krytyczny', HIGH: 'Wysoki', MEDIUM: 'Średni', LOW: 'Niski' }
const STATUS_PL: Record<string, string> = { NEW: 'Nowy', IN_PROGRESS: 'W toku', ANALYSIS: 'Analiza', CLOSED: 'Zamknięty' }
const CATEGORY_PL: Record<string, string> = { UNAUTHORIZED_ACCESS: 'Nieautoryzowany dostęp', DATA_LEAK: 'Wyciek danych', AVAILABILITY: 'Niedostępność', PHISHING: 'Phishing', MALWARE: 'Złośliwe oprogramowanie', PHYSICAL: 'Incydent fizyczny', OTHER: 'Inne' }
const TYPE_PL: Record<string, string> = { HARDWARE: 'Sprzęt', SOFTWARE: 'Oprogramowanie', DATA: 'Dane', CLOUD_SERVICE: 'Usługa cloud', INFRASTRUCTURE: 'Infrastruktura', OTHER: 'Inne' }
const CLASS_PL: Record<string, string> = { RESTRICTED: 'Zastrzeżony', CONFIDENTIAL: 'Poufny', INTERNAL: 'Wewnętrzny', PUBLIC: 'Publiczny' }

const SEVERITY_COLOR: Record<string, string> = { CRITICAL: '#dc2626', HIGH: '#ea580c', MEDIUM: '#d97706', LOW: '#2563eb' }

function fmt(d: Date | string | null | undefined): string {
  if (!d) return '—'
  return new Date(d).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Warsaw' })
}

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default async function PrintIncidentPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const { id } = await params
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const incident = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      actions: { orderBy: { createdAt: 'asc' } },
      evidences: { orderBy: { createdAt: 'asc' } },
      assets: { include: { asset: true } },
      organization: { select: { name: true } },
    },
  })

  if (!incident) notFound()

  const sevColor = SEVERITY_COLOR[incident.severity] || '#555'

  // Elapsed time for NIS2
  let nis2Elapsed = ''
  if (incident.nis2StartedAt) {
    const ms = Date.now() - new Date(incident.nis2StartedAt).getTime()
    const h = Math.floor(ms / (1000 * 60 * 60))
    const d = Math.floor(h / 24)
    nis2Elapsed = d > 0 ? `${d}d ${h % 24}h` : `${h}h`
  }

  const printedAt = new Date().toLocaleString('pl-PL', { timeZone: 'Europe/Warsaw' })
  const orgName = incident.organization?.name || 'Organizacja'

  return (
    <>
      {/* Print button — screen only */}
      <button className="print-btn" onClick={undefined}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        Drukuj / Zapisz PDF
      </button>

      <script dangerouslySetInnerHTML={{ __html: `
        document.querySelector('.print-btn').addEventListener('click', () => window.print());
      `}} />

      <div className="page">

        {/* Document header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', paddingBottom: '16px', borderBottom: '2px solid #1a1a2e' }}>
          <div>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '9pt', color: '#888', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
              {orgName} · SecureDesk
            </div>
            <h1 style={{ fontSize: '18pt', fontWeight: 700, color: '#1a1a2e', lineHeight: 1.2 }}>
              Raport incydentu bezpieczeństwa
            </h1>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '11pt', color: '#3b82f6', fontWeight: 600, marginTop: '4px' }}>
              {incident.incidentNumber}
            </div>
          </div>
          <div style={{ textAlign: 'right', fontSize: '9pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace' }}>
            <div>Wydrukowano: {printedAt}</div>
            <div style={{ marginTop: '4px' }}>DOKUMENT POUFNY</div>
          </div>
        </div>

        {/* Key metadata grid */}
        <div className="section" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0', marginBottom: '24px', border: '1px solid #e5e7eb', borderRadius: '6px', overflow: 'hidden' }}>
          {[
            { label: 'Tytuł incydentu', value: incident.title, span: true },
            { label: 'Ważność', value: SEVERITY_PL[incident.severity] || incident.severity, color: sevColor },
            { label: 'Status', value: STATUS_PL[incident.status] || incident.status },
            { label: 'Kategoria', value: CATEGORY_PL[incident.category] || incident.category },
            { label: 'Zgłaszający', value: incident.reportedBy },
            { label: 'Przypisany do', value: incident.assignedTo || '—' },
            { label: 'Data zgłoszenia', value: fmt(incident.createdAt) },
            { label: 'Data zamknięcia', value: fmt(incident.closedAt) },
            { label: 'Procedura NIS2', value: incident.nis2Active ? `Aktywna (${nis2Elapsed})` : 'Nie dotyczy', color: incident.nis2Active ? '#d97706' : undefined },
          ].map((item, i) => (
            <div key={i} style={{
              padding: '10px 14px',
              borderBottom: i < 6 ? '1px solid #e5e7eb' : 'none',
              borderRight: (item as { span?: boolean }).span ? 'none' : (i % 3 !== 2 ? '1px solid #e5e7eb' : 'none'),
              gridColumn: (item as { span?: boolean }).span ? 'span 3' : undefined,
              background: i % 2 === 0 ? '#fafafa' : '#fff',
            }}>
              <div style={{ fontSize: '8pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px' }}>
                {item.label}
              </div>
              <div style={{ fontSize: '10.5pt', fontWeight: 500, color: item.color || '#1a1a2e' }}>
                {item.value}
              </div>
            </div>
          ))}
        </div>

        {/* Description */}
        <div className="section" style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '11pt', fontWeight: 700, color: '#1a1a2e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'IBM Plex Mono, monospace' }}>
            Opis zdarzenia
          </h2>
          <div style={{ padding: '12px 16px', background: '#fafafa', border: '1px solid #e5e7eb', borderRadius: '4px', fontSize: '10.5pt', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
            {incident.description}
          </div>
        </div>

        {/* NIS2 timeline */}
        {incident.nis2Active && (
          <div className="section" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '11pt', fontWeight: 700, color: '#1a1a2e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'IBM Plex Mono, monospace' }}>
              Procedura NIS2 — Art. 21
            </h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #e5e7eb', borderRadius: '4px' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  {['Krok', 'Wymaganie', 'Termin', 'Data wysłania', 'Status'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '8.5pt', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#555', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { step: '1', req: 'Wczesne ostrzeżenie', deadline: '24h', sent: incident.nis2EarlyWarningSentAt },
                  { step: '2', req: 'Raport do organu nadzoru', deadline: '72h', sent: incident.nis2ReportSentAt },
                  { step: '3', req: 'Raport końcowy', deadline: '30 dni', sent: null },
                ].map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '8px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: '10pt', fontWeight: 600 }}>{row.step}</td>
                    <td style={{ padding: '8px 12px', fontSize: '10pt' }}>{row.req}</td>
                    <td style={{ padding: '8px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: '10pt' }}>{row.deadline}</td>
                    <td style={{ padding: '8px 12px', fontSize: '10pt' }}>{fmt(row.sent)}</td>
                    <td style={{ padding: '8px 12px' }}>
                      <span style={{ fontSize: '9pt', fontWeight: 600, color: row.sent ? '#16a34a' : '#d97706' }}>
                        {row.sent ? '✓ Wysłano' : '○ Oczekuje'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Closure info */}
        {incident.status === 'CLOSED' && (incident.closureRootCause || incident.closureActions || incident.closurePreventive) && (
          <div className="section" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '11pt', fontWeight: 700, color: '#1a1a2e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'IBM Plex Mono, monospace' }}>
              Analiza poinformacyjna
            </h2>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              {incident.closureRootCause && (
                <div style={{ padding: '10px 14px', borderBottom: '1px solid #f0f0f0' }}>
                  <div style={{ fontSize: '8pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', marginBottom: '4px' }}>Przyczyna źródłowa</div>
                  <div style={{ fontSize: '10.5pt', whiteSpace: 'pre-wrap' }}>{incident.closureRootCause}</div>
                </div>
              )}
              {incident.closureActions && (
                <div style={{ padding: '10px 14px', borderBottom: '1px solid #f0f0f0', background: '#fafafa' }}>
                  <div style={{ fontSize: '8pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', marginBottom: '4px' }}>Podjęte działania</div>
                  <div style={{ fontSize: '10.5pt', whiteSpace: 'pre-wrap' }}>{incident.closureActions}</div>
                </div>
              )}
              {incident.closurePreventive && (
                <div style={{ padding: '10px 14px' }}>
                  <div style={{ fontSize: '8pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', marginBottom: '4px' }}>Działania zapobiegawcze</div>
                  <div style={{ fontSize: '10.5pt', whiteSpace: 'pre-wrap' }}>{incident.closurePreventive}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Timeline / Actions */}
        {incident.actions.length > 0 && (
          <div className="section" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '11pt', fontWeight: 700, color: '#1a1a2e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'IBM Plex Mono, monospace' }}>
              Dziennik zdarzeń ({incident.actions.length})
            </h2>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              {incident.actions.map((action, i) => (
                <div key={action.id} style={{ padding: '10px 14px', borderBottom: i < incident.actions.length - 1 ? '1px solid #f0f0f0' : 'none', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '9pt', fontWeight: 600, color: '#3b82f6', fontFamily: 'IBM Plex Mono, monospace' }}>{action.authorName}</span>
                    <span style={{ fontSize: '9pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace' }}>{fmt(action.createdAt)}</span>
                  </div>
                  <div style={{ fontSize: '10pt', color: '#1a1a2e', whiteSpace: 'pre-wrap' }}>{action.content}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Evidence */}
        {incident.evidences.length > 0 && (
          <div className="section" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '11pt', fontWeight: 700, color: '#1a1a2e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'IBM Plex Mono, monospace' }}>
              Dowody ({incident.evidences.length})
            </h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #e5e7eb' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  {['Nazwa pliku', 'Typ', 'Rozmiar', 'Data dodania'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '8.5pt', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#555', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {incident.evidences.map((ev, i) => (
                  <tr key={ev.id} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                    <td style={{ padding: '7px 12px', fontSize: '10pt', fontFamily: 'IBM Plex Mono, monospace' }}>{ev.filename}</td>
                    <td style={{ padding: '7px 12px', fontSize: '10pt', color: '#555' }}>{ev.mimeType}</td>
                    <td style={{ padding: '7px 12px', fontSize: '10pt', fontFamily: 'IBM Plex Mono, monospace' }}>{fmtSize(ev.size)}</td>
                    <td style={{ padding: '7px 12px', fontSize: '10pt' }}>{fmt(ev.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Related assets */}
        {incident.assets.length > 0 && (
          <div className="section" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '11pt', fontWeight: 700, color: '#1a1a2e', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'IBM Plex Mono, monospace' }}>
              Powiązane aktywa ({incident.assets.length})
            </h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #e5e7eb' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  {['Nr aktywa', 'Nazwa', 'Typ', 'Klasyfikacja'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '8.5pt', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#555', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {incident.assets.map((ia, i) => (
                  <tr key={ia.asset.id} style={{ borderBottom: '1px solid #f0f0f0', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                    <td style={{ padding: '7px 12px', fontSize: '10pt', fontFamily: 'IBM Plex Mono, monospace', color: '#2563eb' }}>{ia.asset.assetNumber}</td>
                    <td style={{ padding: '7px 12px', fontSize: '10pt', fontWeight: 500 }}>{ia.asset.name}</td>
                    <td style={{ padding: '7px 12px', fontSize: '10pt', color: '#555' }}>{TYPE_PL[ia.asset.type] || ia.asset.type}</td>
                    <td style={{ padding: '7px 12px', fontSize: '10pt' }}>{CLASS_PL[ia.asset.classification] || ia.asset.classification}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop: '32px', paddingTop: '12px', borderTop: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', fontSize: '8.5pt', color: '#888', fontFamily: 'IBM Plex Mono, monospace' }}>
          <span>{orgName} · SecureDesk · {incident.incidentNumber}</span>
          <span>Wygenerowano: {printedAt}</span>
        </div>

      </div>
    </>
  )
}
