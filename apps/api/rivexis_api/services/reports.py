from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from rivexis_api.models.decision import RivexisDecision


def decision_html(d: RivexisDecision) -> str:
    demo = '<div class="demo">DEMONSTRATION RESULT - NOT LIVE DATA</div>' if d.demo else ''
    why = ''.join(f'<li>{escape(x)}</li>' for x in d.why)
    findings = ''.join(f'<li>{escape(x)}</li>' for x in d.critical_findings) or '<li>No critical findings recorded.</li>'
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><title>Rivexis {escape(d.decision.value)} Report</title>'
        f'<style>body{{font:15px system-ui;max-width:900px;margin:40px auto;color:#10243f}}h1{{color:#0b5cff}}'
        f'.demo{{padding:12px;background:#fff3cd;border:1px solid #eed27a}}.metric{{display:inline-block;margin:8px 24px 8px 0}}'
        f'</style></head><body>{demo}<h1>RIVEXIS Decision Report</h1><p><b>Decision:</b> {escape(d.decision.value)}</p>'
        f'<div class="metric"><b>Risk:</b> {d.overall_risk_score:.1f}/100</div>'
        f'<div class="metric"><b>Decision confidence:</b> {d.decision_confidence:.1f}%</div>'
        f'<div class="metric"><b>Data confidence:</b> {d.data_confidence:.1f}%</div>'
        f'<h2>Executive summary</h2><p>{escape(d.executive_summary)}</p><h2>Why</h2><ul>{why}</ul>'
        f'<h2>Critical findings</h2><ul>{findings}</ul><h2>Recommended action</h2><p>{escape(d.recommended_action)}</p>'
        f'<p><small>Generated from structured Rivexis evidence. Decision ID: {escape(d.decision_id)}</small></p></body></html>'
    )


def _pdf_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor('#DCE8F8'))
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(colors.HexColor('#63748A'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(18 * mm, 9 * mm, 'RIVEXIS - Evidence-grounded decision report')
    canvas.drawRightString(width - 18 * mm, 9 * mm, f'Page {doc.page}')
    canvas.restoreState()


def decision_pdf(d: RivexisDecision) -> bytes:
    """Generate a self-contained server-side PDF report from a structured decision."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f'Rivexis {d.decision.value} Decision Report',
        author='Rivexis',
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RivexisTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor('#0B5CFF'), alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name='Section', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#10243F'), spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name='BodySmall', parent=styles['BodyText'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor('#20344F')))
    styles.add(ParagraphStyle(name='Demo', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=colors.HexColor('#7A4D00'), backColor=colors.HexColor('#FFF3CD'), borderColor=colors.HexColor('#EED27A'), borderWidth=0.5, borderPadding=6, spaceAfter=8))

    story = [Paragraph('RIVEXIS Decision Report', styles['RivexisTitle'])]
    if d.demo:
        story.append(Paragraph('DEMONSTRATION RESULT - NOT LIVE DATA', styles['Demo']))

    metrics = [
        ['Decision', d.decision.value],
        ['Overall risk', f'{d.overall_risk_score:.1f}/100'],
        ['Decision confidence', f'{d.decision_confidence:.1f}%'],
        ['Data confidence', f'{d.data_confidence:.1f}%'],
        ['Timestamp', d.timestamp.isoformat()],
        ['Evidence records', str(d.evidence_count)],
    ]
    table = Table(metrics, colWidths=[48 * mm, 105 * mm], repeatRows=0)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EDF5FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#10243F')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#CCDCEF')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 7 * mm)])

    def section(title: str, body: str):
        story.append(Paragraph(escape(title), styles['Section']))
        story.append(Paragraph(escape(body or 'None recorded.'), styles['BodySmall']))

    def bullets(title: str, items: list[str]):
        story.append(Paragraph(escape(title), styles['Section']))
        if not items:
            story.append(Paragraph('None recorded.', styles['BodySmall']))
            return
        for item in items:
            story.append(Paragraph(f'&bull; {escape(item)}', styles['BodySmall']))

    section('Executive summary', d.executive_summary)
    bullets('Why this decision', d.why)
    bullets('Critical findings', d.critical_findings)
    bullets('Positive findings', d.positive_findings)
    bullets('What could go wrong', d.what_could_go_wrong)
    section('Recommended action', d.recommended_action)
    if d.safer_option:
        section('Safer option', d.safer_option)
    bullets('Assumptions', d.assumptions)
    bullets('Missing data', d.missing_data)

    if d.risk_breakdown:
        heading = Paragraph('Risk breakdown', styles['Section'])
        rows = [['Dimension', 'Risk']] + [[escape(str(k)), f'{float(v):.1f}/100'] for k, v in sorted(d.risk_breakdown.items())]
        t = Table(rows, colWidths=[110 * mm, 43 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10243F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#CCDCEF')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(KeepTogether([heading, t]))

    story.extend([
        Spacer(1, 8 * mm),
        Paragraph(f'Decision ID: {escape(d.decision_id)}', styles['BodySmall']),
        Paragraph('This report explains a structured Rivexis decision. It does not convert missing evidence into certainty.', styles['BodySmall']),
    ])
    doc.build(story, onFirstPage=_pdf_page, onLaterPages=_pdf_page)
    return buf.getvalue()


def protocol_review_html(review: dict) -> str:
    changes = review.get("changes") or []
    rows = "".join(
        f"<tr><td>{escape(str(x.get('materiality','')))}</td><td>{escape(str(x.get('path','')))}</td>"
        f"<td><code>{escape(str(x.get('from')))}</code></td><td><code>{escape(str(x.get('to')))}</code></td></tr>"
        for x in changes
    ) or '<tr><td colspan="4">No configuration changes detected.</td></tr>'
    ident = (review.get("after") or {}).get("deployment_identity") or (review.get("before") or {}).get("deployment_identity") or {}
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>Rivexis Protocol Configuration Review</title>'
        '<style>body{font:14px system-ui;max-width:1100px;margin:36px auto;color:#10243f}h1{color:#0b5cff}'
        'table{border-collapse:collapse;width:100%}th,td{border:1px solid #d7e2f0;padding:8px;vertical-align:top}'
        'th{background:#10243f;color:white}code{white-space:pre-wrap;word-break:break-all}</style></head><body>'
        f'<h1>RIVEXIS Protocol Configuration Review</h1><p><b>Adapter:</b> {escape(str(review.get("adapter")))} &nbsp; '
        f'<b>Chain:</b> {escape(str(review.get("chain")))} &nbsp; <b>Blocks:</b> {escape(str(review.get("from_block")))} → {escape(str(review.get("to_block")))}</p>'
        f'<p><b>Deployment identity:</b> {escape(str(ident.get("status") or "UNVERIFIED"))} &nbsp; '
        f'<b>Changes:</b> {len(changes)}</p>'
        '<table><thead><tr><th>Materiality</th><th>Path</th><th>Before</th><th>After</th></tr></thead><tbody>'
        f'{rows}</tbody></table><p><small>Materiality is a deterministic Rivexis review priority, not a claim of maliciousness or safety.</small></p></body></html>'
    )


def protocol_review_pdf(review: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm, topMargin=16*mm, bottomMargin=18*mm,
                            title='Rivexis Protocol Configuration Review', author='Rivexis')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='P10Title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=18, leading=22,
                              textColor=colors.HexColor('#0B5CFF'), alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name='P10Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=8.5, leading=11,
                              textColor=colors.HexColor('#20344F')))
    story=[Paragraph('RIVEXIS Protocol Configuration Review',styles['P10Title'])]
    story.append(Paragraph(
        f"Adapter: {escape(str(review.get('adapter')))} | Chain: {escape(str(review.get('chain')))} | "
        f"Blocks: {escape(str(review.get('from_block')))} to {escape(str(review.get('to_block')))}",
        styles['P10Body']))
    counts=review.get('materiality_counts') or {}
    story.append(Paragraph(f"Detected changes: {review.get('change_count',0)} | HIGH {counts.get('HIGH',0)} | MEDIUM {counts.get('MEDIUM',0)} | LOW {counts.get('LOW',0)}",styles['P10Body']))
    story.append(Spacer(1,4*mm))
    rows=[['Priority','Configuration path','Before','After']]
    for item in review.get('changes') or []:
        rows.append([
            str(item.get('materiality','')), Paragraph(escape(str(item.get('path',''))),styles['P10Body']),
            Paragraph(escape(str(item.get('from'))),styles['P10Body']), Paragraph(escape(str(item.get('to'))),styles['P10Body'])
        ])
    if len(rows)==1: rows.append(['—','No configuration changes detected.','',''])
    table=Table(rows,colWidths=[18*mm,55*mm,52*mm,52*mm],repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#10243F')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCDCEF')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    story.append(table)
    story.append(Spacer(1,5*mm))
    story.append(Paragraph('Materiality is a deterministic review priority. Historical state depends on archive-capable RPC evidence.',styles['P10Body']))
    doc.build(story,onFirstPage=_pdf_page,onLaterPages=_pdf_page)
    return buf.getvalue()


def protocol_investigation_html(case: dict) -> str:
    payload=case.get("payload") or case
    timeline=payload.get("timeline") or {}; events=timeline.get("events") or []
    event_rows="".join(
        f"<tr><td>{escape(str(e.get('block_number','—')))}</td><td>{escape(str(e.get('event','')))}</td><td>{escape(str(e.get('category','')))}</td><td><code>{escape(str(e.get('transaction_hash','')))}</code></td></tr>"
        for e in events
    ) or '<tr><td colspan="4">No normalized events recorded in this case.</td></tr>'
    reviews=", ".join(escape(str(x)) for x in payload.get("review_ids") or []) or "None"
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>Rivexis Protocol Investigation</title>'
        '<style>body{font:14px system-ui;max-width:1100px;margin:36px auto;color:#10243f}h1{color:#0b5cff}'
        'table{border-collapse:collapse;width:100%}th,td{border:1px solid #d7e2f0;padding:8px;vertical-align:top}'
        'th{background:#10243f;color:white}code{word-break:break-all}.muted{color:#607086}</style></head><body>'
        f'<h1>RIVEXIS Protocol Investigation</h1><p><b>Case:</b> {escape(str(case.get("id","")))} &nbsp; <b>Status:</b> {escape(str(case.get("status","")))}</p>'
        f'<h2>{escape(str(payload.get("title") or "Untitled investigation"))}</h2>'
        f'<p><b>Disposition:</b> {escape(str(payload.get("disposition") or "Not set"))}</p>'
        f'<p><b>Linked configuration reviews:</b> {reviews}</p><p><b>Notes:</b> {escape(str(payload.get("notes") or "None"))}</p>'
        '<h3>Normalized protocol timeline</h3><table><thead><tr><th>Block</th><th>Event</th><th>Category</th><th>Transaction</th></tr></thead><tbody>'
        f'{event_rows}</tbody></table><p class="muted">This case preserves analyst workflow and evidence references; closing a case is not a protocol-safety certification.</p></body></html>'
    )

def protocol_investigation_pdf(case: dict) -> bytes:
    payload=case.get("payload") or case; timeline=payload.get("timeline") or {}; events=timeline.get("events") or []
    buf=BytesIO();doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=14*mm,leftMargin=14*mm,topMargin=16*mm,bottomMargin=18*mm,title='Rivexis Protocol Investigation',author='Rivexis')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='P11Title',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=18,leading=22,textColor=colors.HexColor('#0B5CFF'),alignment=TA_CENTER,spaceAfter=8));styles.add(ParagraphStyle(name='P11Body',parent=styles['BodyText'],fontName='Helvetica',fontSize=8.5,leading=11,textColor=colors.HexColor('#20344F')))
    story=[Paragraph('RIVEXIS Protocol Investigation',styles['P11Title']),Paragraph(escape(str(payload.get('title') or 'Untitled investigation')),styles['Heading2'])]
    story.append(Paragraph(f"Case: {escape(str(case.get('id','')))} | Status: {escape(str(case.get('status','')))}",styles['P11Body']))
    story.append(Paragraph(f"Disposition: {escape(str(payload.get('disposition') or 'Not set'))}",styles['P11Body']))
    story.append(Paragraph(f"Linked reviews: {escape(', '.join(str(x) for x in payload.get('review_ids') or []) or 'None')}",styles['P11Body']))
    story.append(Paragraph(f"Notes: {escape(str(payload.get('notes') or 'None'))}",styles['P11Body']));story.append(Spacer(1,4*mm))
    rows=[['Block','Event','Category','Transaction']]
    for e in events[:250]:rows.append([str(e.get('block_number','—')),str(e.get('event','')),str(e.get('category','')),Paragraph(escape(str(e.get('transaction_hash',''))),styles['P11Body'])])
    if len(rows)==1:rows.append(['—','No normalized events recorded','',''])
    t=Table(rows,colWidths=[24*mm,45*mm,38*mm,70*mm],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#10243F')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCDCEF')),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(t);story.append(Spacer(1,4*mm));story.append(Paragraph('Case disposition records analyst workflow and does not certify protocol safety.',styles['P11Body']))
    doc.build(story,onFirstPage=_pdf_page,onLaterPages=_pdf_page);return buf.getvalue()
