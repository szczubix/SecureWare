export default function PrintLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

          * { box-sizing: border-box; margin: 0; padding: 0; }

          body {
            font-family: 'IBM Plex Sans', Arial, sans-serif;
            background: #fff;
            color: #1a1a2e;
            font-size: 11pt;
            line-height: 1.5;
          }

          @media screen {
            body { background: #f5f5f5; padding: 20px; }
            .page { background: #fff; max-width: 210mm; margin: 0 auto; padding: 20mm; box-shadow: 0 2px 20px rgba(0,0,0,0.15); border-radius: 4px; }
            .print-btn {
              position: fixed; top: 16px; right: 16px;
              padding: 10px 20px; background: #3b82f6; color: #fff;
              border: none; border-radius: 6px; font-size: 13px; font-weight: 600;
              cursor: pointer; display: flex; align-items: center; gap: 8px;
              box-shadow: 0 2px 8px rgba(59,130,246,0.4);
              z-index: 100;
            }
            .print-btn:hover { background: #2563eb; }
          }

          @media print {
            body { background: #fff; padding: 0; }
            .page { padding: 15mm; max-width: 100%; box-shadow: none; }
            .print-btn { display: none !important; }
            .no-print { display: none !important; }
            h2 { page-break-after: avoid; }
            .section { page-break-inside: avoid; }
            tr { page-break-inside: avoid; }
          }

          @page {
            size: A4;
            margin: 15mm 15mm 15mm 15mm;
          }
        `}</style>
      </head>
      <body>
        {children}
      </body>
    </html>
  )
}
