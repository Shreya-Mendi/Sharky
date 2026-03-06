"use client";

export interface MemoSection {
  title: string;
  body: string;
}

export function exportICMemoPdf(title: string, sections: MemoSection[]) {
  const timestamp = new Date().toLocaleString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const sectionHtml = sections
    .map(
      (s) => `
      <section class="section">
        <h2>${s.title}</h2>
        <div class="body">${s.body.replace(/\n/g, "<br/>")}</div>
      </section>
    `
    )
    .join('<div class="divider"></div>');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
      color: #111827;
      background: #fff;
      padding: 48px 56px;
      max-width: 860px;
      margin: 0 auto;
      font-size: 14px;
      line-height: 1.6;
    }

    .header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      border-bottom: 2px solid #111827;
      padding-bottom: 18px;
      margin-bottom: 28px;
    }

    .header-left .label {
      font-size: 10px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #6b7280;
      font-weight: 500;
    }

    .header-left h1 {
      font-size: 22px;
      font-weight: 700;
      color: #111827;
      margin-top: 6px;
      line-height: 1.2;
    }

    .header-right {
      text-align: right;
      font-size: 11px;
      color: #6b7280;
      line-height: 1.7;
    }

    .header-right .brand {
      font-weight: 600;
      color: #374151;
    }

    .section {
      margin-bottom: 24px;
    }

    .section h2 {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #6b7280;
      margin-bottom: 8px;
    }

    .section .body {
      font-size: 13.5px;
      color: #1f2937;
      line-height: 1.7;
    }

    .divider {
      height: 1px;
      background: #e5e7eb;
      margin: 20px 0;
    }

    .footer {
      margin-top: 36px;
      padding-top: 14px;
      border-top: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: #9ca3af;
    }

    @media print {
      body { padding: 0; }
      .header { page-break-after: avoid; }
      .section { page-break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      <p class="label">Investment Committee Memo</p>
      <h1>${title}</h1>
    </div>
    <div class="header-right">
      <p class="brand">DealScope</p>
      <p>Generated ${timestamp}</p>
      <p>Confidential — for internal use only</p>
    </div>
  </div>

  ${sectionHtml}

  <div class="footer">
    <span>DealScope — Pitch Dynamics Intelligence</span>
    <span>Signals derived from pitch transcript corpus. Not a guarantee of investment outcomes.</span>
  </div>
</body>
</html>`;

  const win = window.open("", "_blank");
  if (!win) return;
  win.document.write(html);
  win.document.close();
  win.focus();
  // Small delay so fonts load before print dialog
  setTimeout(() => win.print(), 400);
}
