from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import pandas as pd
import io

def generate_pdf_report(tally_data, total_items, total_value):
    """
    Generates a PDF inventory report inside a BytesIO buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1e1b4b'),
        spaceAfter=15
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=25
    )

    # Title & Metadata
    story.append(Paragraph("Smart Inventory Counter - Stock Report", title_style))
    from datetime import datetime
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Unique Types: {len(tally_data)}", meta_style))
    story.append(Spacer(1, 10))

    # Summary table
    summary_data = [
        ["Total Stock Quantity Checked", str(total_items)],
        ["Estimated Valuation", f"${total_value:.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[200, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 25))

    # Items table
    table_content = [["Detected Class", "SKU Name", "Count", "Unit Price", "Subtotal", "Alert Status"]]
    for item in tally_data:
        table_content.append([
            item.get("Detected Class", "N/A"),
            item.get("SKU Name", "N/A"),
            str(item.get("Count", 0)),
            item.get("Price ($)", "$0.00"),
            item.get("Subtotal", "$0.00"),
            item.get("Status", "OK")
        ])

    items_table = Table(table_content, colWidths=[100, 150, 60, 70, 70, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(items_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_csv_report(tally_data):
    """
    Generates a CSV string representation of the scan results.
    """
    df = pd.DataFrame(tally_data)
    # Clean raw columns for output
    cols_to_keep = [c for c in ["Detected Class", "SKU Name", "Count", "Price ($)", "Subtotal", "Status"] if c in df.columns]
    return df[cols_to_keep].to_csv(index=False)
