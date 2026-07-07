from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd
import io
import os
from datetime import datetime

import urllib.request

REGULAR_FONT_FILE = "NotoSansTamil-Regular.ttf"
BOLD_FONT_FILE = "NotoSansTamil-Bold.ttf"

if not os.path.exists(REGULAR_FONT_FILE):
    script_regular = os.path.join(os.path.dirname(__file__), "NotoSansTamil-Regular.ttf")
    if os.path.exists(script_regular):
        REGULAR_FONT_FILE = script_regular
    else:
        try:
            urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/notosanstamil/static/NotoSansTamil-Regular.ttf", REGULAR_FONT_FILE)
        except Exception:
            pass

if not os.path.exists(BOLD_FONT_FILE):
    script_bold = os.path.join(os.path.dirname(__file__), "NotoSansTamil-Bold.ttf")
    if os.path.exists(script_bold):
        BOLD_FONT_FILE = script_bold
    else:
        try:
            urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/notosanstamil/static/NotoSansTamil-Bold.ttf", BOLD_FONT_FILE)
        except Exception:
            pass

try:
    pdfmetrics.registerFont(TTFont('NotoSansTamil', REGULAR_FONT_FILE))
    pdfmetrics.registerFont(TTFont('NotoSansTamil-Bold', BOLD_FONT_FILE))
    DEFAULT_FONT = 'NotoSansTamil'
    DEFAULT_BOLD_FONT = 'NotoSansTamil-Bold'
except Exception:
    DEFAULT_FONT = 'Helvetica'
    DEFAULT_BOLD_FONT = 'Helvetica-Bold'

def generate_pdf_report(tally_data, total_items, total_value, translations, lang):
    """
    Generates a PDF inventory report inside a BytesIO buffer supporting English and Tamil.
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
        fontName=DEFAULT_BOLD_FONT,
        fontSize=22,
        textColor=colors.HexColor('#1e1b4b'),
        spaceAfter=15
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=25
    )
    
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=9,
        textColor=colors.HexColor('#0f172a')
    )

    header_cell_style = ParagraphStyle(
        'HeaderCellStyle',
        parent=styles['Normal'],
        fontName=DEFAULT_BOLD_FONT,
        fontSize=10,
        textColor=colors.whitesmoke
    )

    # Title & Metadata
    report_title = f"{translations['English']['title']} - {translations['English']['Item List']}"
    story.append(Paragraph(report_title, title_style))
    
    timestamp_str = f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    story.append(Paragraph(timestamp_str, meta_style))
    story.append(Spacer(1, 10))

    # Summary table
    summary_data = [
        [Paragraph(translations["English"]["Items Counted"], cell_style), Paragraph(str(total_items), cell_style)],
        [Paragraph(translations["English"]["Total Value"], cell_style), Paragraph(f"Rs. {total_value:.2f}", cell_style)]
    ]
    summary_table = Table(summary_data, colWidths=[200, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 25))

    # Items table headers
    headers = [
        Paragraph(translations["English"]["Product Name"], header_cell_style),
        Paragraph(translations["English"]["Item"], header_cell_style),
        Paragraph(translations["English"]["Current Count"], header_cell_style),
        Paragraph(translations["English"]["Price"], header_cell_style),
        Paragraph(translations["English"]["Min Item"], header_cell_style),
        Paragraph(translations["English"]["Status"], header_cell_style)
    ]
    table_content = [headers]
    
    # Items table data
    for item in tally_data:
        raw_status = item.get("status", "N/A")
        if raw_status in [translations["Tamil"]["Low Stock"], translations["English"]["Low Stock"], "Low Stock", "Low", "குறைவு"]:
            pdf_status = "Low"
        else:
            pdf_status = "Good"
            
        table_content.append([
            Paragraph(str(item.get("sku_name", "N/A")), cell_style),
            Paragraph(str(item.get("class_id", "N/A")), cell_style),
            Paragraph(str(item.get("count", 0)), cell_style),
            Paragraph(f"Rs. {item.get('price', 0.0):.2f}", cell_style),
            Paragraph(str(item.get("min_item", 0)), cell_style),
            Paragraph(pdf_status, cell_style)
        ])

    items_table = Table(table_content, colWidths=[130, 80, 70, 80, 80, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#7c3aed')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(items_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_csv_report(tally_data, translations, lang):
    """
    Generates a CSV string representation of the scan results supporting English and Tamil.
    """
    csv_data = []
    for item in tally_data:
        csv_data.append({
            translations[lang]["Product Name"]: item.get("sku_name", "N/A"),
            translations[lang]["Item"]: item.get("class_id", "N/A"),
            translations[lang]["Current Count"]: item.get("count", 0),
            translations[lang]["Price"]: f"Rs. {item.get('price', 0.0):.2f}",
            translations[lang]["Min Item"]: item.get("min_item", 0),
            translations[lang]["Status"]: item.get("status", "N/A")
        })
    df = pd.DataFrame(csv_data)
    return df.to_csv(index=False)
