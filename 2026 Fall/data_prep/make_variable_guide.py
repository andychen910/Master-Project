#!/usr/bin/env python3
"""Create a Word guide to project variables, based on the Oct. 6 proposal."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data_prep" / "Master_Project_Variable_Guide.docx"


def set_cell(cell, value):
    cell.text = value
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        set_cell(table.rows[0].cells[i], header)
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
        for paragraph in table.rows[0].cells[i].paragraphs:
            paragraph.paragraph_format.space_after = Pt(0)
        shading = __import__("docx.oxml").oxml.parse_xml(
            r'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="24476B"/>'
        )
        table.rows[0].cells[i]._tc.get_or_add_tcPr().append(shading)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], str(value))
            for paragraph in cells[i].paragraphs:
                paragraph.paragraph_format.space_after = Pt(2)
                paragraph.paragraph_format.space_before = Pt(2)
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    if widths:
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Inches(width)
    document.add_paragraph()
    return table


def add_bullet(document, text):
    p = document.add_paragraph(style="List Bullet")
    p.add_run(text)
    return p


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.65)
section.bottom_margin = Inches(0.65)
section.left_margin = Inches(0.7)
section.right_margin = Inches(0.7)

styles = doc.styles
styles["Normal"].font.name = "Arial"
styles["Normal"].font.size = Pt(10)
styles["Normal"].paragraph_format.space_after = Pt(5)
for style_name in ("Title", "Heading 1", "Heading 2"):
    styles[style_name].font.name = "Arial"

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("Master’s Project Variable Guide")
run.bold = True
run.font.size = Pt(20)
run.font.color.rgb = RGBColor(36, 71, 107)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.add_run("Based on Andy Chen’s proposal dated October 6, 2026").italic = True

doc.add_heading("1. Project design at a glance", level=1)
doc.add_paragraph(
    "The proposal studies how interest-rate changes are associated with U.S. housing-price growth, "
    "how the response develops over time, and whether it differs across seven states. It uses a "
    "monthly national analysis and a quarterly state panel. The main outcome is house-price growth. "
    "Housing starts (HOUST) is a secondary national outcome only."
)
add_table(doc, ["Analysis", "Frequency and source", "Main outcome", "Main purpose"], [
    ["National baseline and distributed lag", "Monthly FRED-MD plus S&P/Case-Shiller national HPI", "National HPI growth", "Estimate the timing of the national association with rate changes."],
    ["State heterogeneity", "Quarterly FHFA state HPI plus FRED-QD controls", "State HPI log growth", "Test whether responses differ across the seven states."],
    ["Robustness", "Alternative measures or samples where available", "Depends on specification", "Check whether the main patterns are sensitive to reasonable choices."],
])

doc.add_heading("2. Main national monthly variables", level=1)
monthly_rows = [
    ["CSUSHPINSA", "S&P/Case-Shiller U.S. National Home Price Index, not seasonally adjusted.", "Index points; not dollars.", "Main price measure. Convert to log growth. The proposal’s primary measure is year-over-year log growth: 100 × [ln(HPIₜ) − ln(HPIₜ₋₁₂)].", "Primary dependent variable."],
    ["FEDFUNDS", "Effective Federal Funds Rate.", "Percent per year.", "Use the monthly change, ΔFEDFUNDS = FEDFUNDSₜ − FEDFUNDSₜ₋₁, for the main rate measure.", "Primary explanatory variable; include current and lagged changes in the distributed-lag model."],
    ["GS10", "10-year U.S. Treasury constant-maturity yield.", "Percent per year.", "Use changes as an alternative interest-rate measure; its change is in percentage points.", "Robustness or alternative rate specification."],
    ["CPIAUCSL", "Consumer Price Index for All Urban Consumers, seasonally adjusted.", "Price index, 1982–84 = 100.", "FRED-MD code 6: second difference of the natural log. For an interpretable inflation control, derive year-over-year CPI inflation from the untransformed level and document that choice.", "Candidate control. The raw level and FRED-MD transformed series answer different questions."],
    ["UNRATE", "Civilian unemployment rate.", "Percent of the labor force.", "FRED-MD code 2: first difference. The rate level can also be used if justified and checked for stationarity.", "Candidate labor-market control."],
    ["PAYEMS", "Total nonfarm payroll employment.", "Thousands of jobs, seasonally adjusted.", "FRED-MD code 5: first difference of the natural log, approximately monthly growth.", "Candidate labor-market control; use a clearly named transformed field."],
    ["HOUST", "New privately owned housing units started.", "Thousands of units at a seasonally adjusted annual rate.", "FRED-MD code 4: first difference of the squared series. Keep this as a secondary outcome only if analyzed; do not label it state-specific activity.", "Optional secondary national housing-activity outcome."],
]
add_table(doc, ["Code", "Definition", "Unit", "Transformation and interpretation", "Model role"], monthly_rows, [0.9, 1.55, 1.0, 2.65, 1.25])

doc.add_heading("3. Main state-panel variables", level=1)
state_rows = [
    ["state", "Two-letter state identifier: AZ, CA, FL, IL, NY, OH, TX.", "Category", "Identifies the state in each panel row. State fixed effects account for stable average differences."],
    ["quarter", "Calendar quarter shared by the state HPI and quarterly macro data.", "YYYYQn", "Panel time key. Each state-quarter should appear once."],
    ["hpi", "FHFA state house-price index level.", "Index points; not dollars.", "Original index level. Preserve for reference; its scale differs across states and should not be compared as a dollar price."],
    ["hpi_log_growth", "Quarter-over-quarter log change in the state HPI.", "Log points; multiply by 100 for approximate percent growth.", "ln(HPIₜ) − ln(HPIₜ₋₁). First observation per state is missing by construction."],
    ["FEDFUNDS / FEDFUNDS_transformed", "Quarterly federal funds rate and its FRED-QD transformation.", "Percent per year / percentage-point change.", "In the current quarterly file, code 2 means first difference. This is a candidate panel rate variable, subject to alignment with the proposal’s quarterly design."],
    ["CPIAUCSL / CPIAUCSL_transformed", "Quarterly CPI and its FRED-QD transformation.", "Index / transformed log-change units.", "In the current quarterly file, code 6 means second difference of log CPI. A first-difference log CPI measure is often easier to interpret as inflation; define the selected control explicitly."],
    ["GS10 / GS10_transformed", "Quarterly 10-year Treasury yield and its FRED-QD transformation.", "Percent per year / percentage-point change.", "In the current quarterly file, code 2 means first difference; treat as an alternative rate measure."],
    ["covid", "Indicator equal to 1 from 2020 Q1 onward and 0 before.", "Binary: 0 or 1.", "Optional robustness variable. The proposal treats COVID analysis as secondary, not part of the main model by default."],
]
add_table(doc, ["Field", "Definition", "Unit", "Interpretation and use"], state_rows, [1.55, 2.2, 1.25, 2.35])

doc.add_heading("4. Other columns in the current prepared files", level=1)
doc.add_paragraph(
    "The current quarterly preparation script also exports PERMIT and PAYEMS, each with an original "
    "and transformed field. PERMIT means new private housing units authorized by building permits, "
    "measured at a seasonally adjusted annual rate in thousands of units. In the March 2026 FRED-QD "
    "file its transformation code is 5, the first difference of the natural log. PAYEMS is also code 5. "
    "These are candidate controls or descriptive series; the October 6 proposal’s core list names "
    "UNRATE, so UNRATE should be added to the quarterly preparation before estimating the proposed panel model."
)
doc.add_paragraph(
    "In national_quarterly.csv, the fields ending in _transformed apply the FRED-QD transformation "
    "listed in that file’s metadata. In state_panel_long.csv, HOUST and PERMIT are repeated across "
    "states for the same quarter because they are national series. This repetition does not create "
    "state-level housing starts or permits."
)

doc.add_heading("5. Dataset and sample notes", level=1)
add_bullet(doc, "Current prepared quarterly files use 2026-03-QD.csv and cover 1959 Q1 to 2025 Q4 for national series.")
add_bullet(doc, "The state panel currently contains 204 quarters per state from 1975 Q1 to 2025 Q4, 1,428 rows total.")
add_bullet(doc, "The October 6 proposal’s main national monthly analysis requires 2026-02-MD.csv and CSUSHPINSA_MD.csv. Those monthly variables are not yet included in the current prepared output.")
add_bullet(doc, "The proposal’s comparable main sample begins in 1987, when the national monthly HPI begins. Earlier state observations can be retained for descriptive analysis but should not silently extend the comparable sample.")
add_bullet(doc, "Store raw observations and transformed variables under distinct names. Record units and transformation formulas in analysis code and tables.")

doc.add_heading("6. Source files", level=1)
for source in [
    "2026 spring/Andy_Chen_Proposal_10:6:2026.docx, proposal version dated October 6, 2026.",
    "dataset/2026-02-MD.csv, FRED-MD monthly vintage.",
    "dataset/2026-03-QD.csv, FRED-QD quarterly vintage.",
    "dataset/CSUSHPINSA_MD.csv, monthly national S&P/Case-Shiller HPI.",
    "dataset/AZSTHPI.csv, CASTHPI.csv, FLSTHPI.csv, ILSTHPI.csv, NYSTHPI.csv, OHSTHPI.csv, TXSTHPI.csv, FHFA state HPI files.",
]:
    add_bullet(doc, source)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.add_run("Master’s Project | Variable definitions follow the October 6, 2026 proposal")

doc.save(OUTPUT)
print(OUTPUT)
