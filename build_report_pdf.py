"""
Generate Lab_3_Report_Kareem_Alaa.pdf with ReportLab.
Optimized layout so Section 7 and its screenshot are kept together,
producing a tightly formatted 5-page report.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#71717A")) # Zinc-500

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(48, 11 * 72 - 32, "INF4058 Data Engineering - Lab 3 Assignment Report")
            self.drawRightString(8.5 * 72 - 48, 11 * 72 - 32, "Kareem Alaa Mohamed (ID: 692300273)")
            self.setStrokeColor(colors.HexColor("#E4E4E7"))
            self.setLineWidth(0.5)
            self.line(48, 11 * 72 - 36, 8.5 * 72 - 48, 11 * 72 - 36)

        # Footer (All pages)
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 48, 26, footer_text)
        self.drawString(48, 26, "NYC Taxi Data Profiling & Cleaning Pipeline | Submission Document")
        self.setStrokeColor(colors.HexColor("#E4E4E7"))
        self.setLineWidth(0.5)
        self.line(48, 36, 8.5 * 72 - 48, 36)
        
        self.restoreState()


def create_pdf_report(filename="Lab_3_Report_Kareem_Alaa.pdf"):
    # Margins 40pt
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0F172A") # Slate-900
    accent_blue = colors.HexColor("#1D4ED8")   # Blue-700
    body_color = colors.HexColor("#334155")    # Slate-700

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=accent_blue,
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=accent_blue,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=body_color,
        spaceAfter=4
    )

    code_caption_style = ParagraphStyle(
        "CodeCaption",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#475569"),
        spaceBefore=2,
        spaceAfter=4,
        alignment=1 # Center
    )

    story = []

    # ==========================================
    # SECTION 1: COVER
    # ==========================================
    story.append(Paragraph("INF4058 DATA ENGINEERING | LAB 3 ASSIGNMENT", subtitle_style))
    story.append(Paragraph("NYC Taxi Data Profiling & Cleaning Pipeline", title_style))
    story.append(Paragraph("<b>Goal:</b> Clean the NYC Taxi data, profile anomalies in chunks of 100k, and stop at cleaning stage.", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=3, spaceAfter=8))

    meta_data = [
        [
            Paragraph("<b>Student Name:</b> Kareem Alaa Mohamed", body_style),
            Paragraph("<b>Student ID:</b> 692300273", body_style),
        ],
        [
            Paragraph("<b>Course:</b> INF4058 Data Engineering", body_style),
            Paragraph("<b>Due Date:</b> 19th of October 2026, 11:59 PM", body_style),
        ],
        [
            Paragraph("<b>Dataset:</b> yellow_tripdata_2021-01.csv.gz (1,369,765 rows)", body_style),
            Paragraph("<b>GitHub Repo:</b> <font color='#1D4ED8'><u>https://github.com/Kimobest/NYC-Taxi-Data-Profiling-Cleaning</u></font>", body_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 260])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 2: THE FLOW, IN YOUR WORDS
    # ==========================================
    story.append(Paragraph("Section 2: The Flow, in Your Words", h1_style))
    story.append(Paragraph(
        "Data engineering pipelines follow the lifecycle: <b>Source &rarr; Extract &rarr; Transform &rarr; Load &rarr; Serve</b>. "
        "Below is how our laboratory pipeline operates across each distinct stage:",
        body_style
    ))

    flow_stages = [
        ("Source", "Raw compressed CSV file (<code>yellow_tripdata_2021-01.csv.gz</code>) hosted on GitHub release storage, containing 1,369,765 uncleaned trip records generated by NYC Yellow Cabs in January 2021."),
        ("Extract", "The script <code>ingest_data.py</code> pulls data directly via HTTP streams using <code>pandas.read_csv()</code> in iterator chunks of 100,000 rows, avoiding large local disk writes."),
        ("Transform", "Type coercion using explicit schema mappings (<code>Int64</code> and <code>parse_dates</code>), temporal boundary filtering, anomaly detection, and business logic execution inside <code>clean(df)</code>."),
        ("Load", "Streaming chunk inserts into PostgreSQL database via SQLAlchemy engine. Chunk 1 initializes table DDL with <code>if_exists='replace'</code>, while chunks 2 through 14 use <code>if_exists='append'</code>."),
        ("Serve", "PostgreSQL exposes tabular data on port 5432 to pgAdmin (port 8085), analytics queries, and downstream visualization dashboards.")
    ]

    for title, desc in flow_stages:
        story.append(Paragraph(f"<b>&bull; {title}:</b> {desc}", body_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Component Roles & Technical Rationale:", h2_style))
    story.append(Paragraph(
        "<b>1. ingest_data.py:</b> CLI ingestion engine built with <code>click</code> and <code>SQLAlchemy</code>. Manages network extraction, iterator chunking, schema enforcement, and database transactions.<br/>"
        "<b>2. docker-compose.yaml:</b> Orchestrates two container services: <code>pgdatabase</code> (PostgreSQL 18 with persistent volume <code>ny_taxi_postgres_data</code> on port 5432) and <code>pgadmin</code> (port 8085), creating a shared bridge network for automatic service DNS resolution.<br/>"
        "<b>3. Dockerfile:</b> Builds a slim execution environment (<code>python:3.13-slim</code>) using Astral <code>uv</code> to lock exact dependencies, providing reproducible, zero-drift pipeline execution.<br/>"
        "<b>Why chunks?</b> Prevents Out-Of-Memory (OOM) crashes. 100k-row chunks maintain a constant ~120 MB RAM footprint regardless of whether the file has 1.3 million rows or 100 million rows.<br/>"
        "<b>Why Int64?</b> Standard NumPy <code>int64</code> cannot store nulls. When missing values appear in chunks 13-14 for <code>passenger_count</code> and <code>VendorID</code>, standard Pandas forces the column to <code>float64</code> (e.g. <code>1.0</code>). Nullable <code>Int64</code> preserves relational integer schema integrity alongside <code>&lt;NA&gt;</code>.<br/>"
        "<b>Why replace on the first chunk?</b> Creates table schema DDL cleanly on the initial batch. Subsequent chunks switch to <code>if_exists='append'</code> so previous chunks are preserved rather than overwritten.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 3: WHAT WE RAN IN CLASS
    # ==========================================
    story.append(Paragraph("Section 3: What We Ran in Class", h1_style))
    story.append(Paragraph(
        "<b>1. Compose up:</b> We ran <code>docker compose up -d</code> to launch the PostgreSQL 18 container and pgAdmin service in detached mode on an isolated bridge network.<br/>"
        "<b>2. Docker build:</b> We ran <code>docker build -t taxi_ingest:v001 .</code> to compile our Python script and uv dependency environment into an immutable image.<br/>"
        "<b>3. Container run into yellow_taxi_trips:</b> We ran <code>docker run --network=01-docker-terraform_default taxi_ingest:v001 ...</code> which ingested all 14 chunks, and verified in PostgreSQL that <code>SELECT COUNT(*) FROM yellow_taxi_trips;</code> returned exactly <b>1,369,765</b> rows.",
        body_style
    ))

    inclass_img_path = "screenshots/step3_in_class_run.png"
    if os.path.exists(inclass_img_path):
        story.append(Image(inclass_img_path, width=530, height=140))
        story.append(Paragraph("<b>Evidence 3.1:</b> Terminal commands, container build, progress bar (14/14), and database count verification (1,369,765).", code_caption_style))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 4: WHAT YOU FOUND IN THE DATA
    # ==========================================
    story.append(Paragraph("Section 4: What You Found in the Data (Profiling & Anomalies)", h1_style))
    story.append(Paragraph(
        "We profiled the entire dataset of <b>1,369,765 rows</b> in chunks of 100,000 without loading it all into memory at once. "
        "The profiling script computed null counts, dtypes, minimums, and maximums across all 18 columns, uncovering severe data anomalies:<br/>"
        "&bull; <b>Null Values:</b> Exactly <b>98,352 rows (7.18%)</b> have missing values across <code>VendorID</code>, <code>passenger_count</code>, <code>RatecodeID</code>, <code>store_and_fwd_flag</code>, and <code>payment_type</code> simultaneously (unmetered dispatch records).<br/>"
        "&bull; <b>Invalid Dates:</b> <b>24 rows</b> feature pickup timestamps outside January 2021 (ranging from <code>2008-12-31</code> to late February 2021). Furthermore, <b>5,642 rows</b> feature 'time travel' where dropoff occurs before pickup.<br/>"
        "&bull; <b>Odd & Extreme Values:</b> <b>6,769 negative fares</b> (minimum -$490.00 dispute chargebacks), <b>642 zero fares</b>, <b>19,952 zero-distance trips</b>, <b>55 trips &gt; 100 miles</b> (including an impossible 263,163.28-mile GPS glitch), and <b>36 records</b> with invalid <code>RatecodeID = 99</code>.<br/>"
        "&bull; <b>Duplicates:</b> 0 exact duplicates across all 18 columns, but <b>5,900 duplicate ride keys</b>.",
        body_style
    ))

    # Evidence 4.1 Step 1 Look
    look_img_path = "screenshots/step1_look.png"
    if os.path.exists(look_img_path):
        story.append(Image(look_img_path, width=530, height=140))
        story.append(Paragraph("<b>Evidence 4.1 (Step 1):</b> Printed df.head() and df.dtypes from the first 100 rows.", code_caption_style))

    # Evidence 4.2 Step 2 Profile
    prof_img_path = "screenshots/step2_profile.png"
    if os.path.exists(prof_img_path):
        story.append(Image(prof_img_path, width=530, height=155))
        story.append(Paragraph("<b>Evidence 4.2 (Step 2):</b> Printed profiling table across all 1,369,765 rows (dtype, nulls, min, max).", code_caption_style))

    # Evidence 4.3 Step 3 Problems
    prob_img_path = "screenshots/step3_problems.png"
    if os.path.exists(prob_img_path):
        story.append(Image(prob_img_path, width=530, height=130))
        story.append(Paragraph("<b>Evidence 4.3 (Step 3):</b> Printed table of data quality anomalies and counts detected across chunks.", code_caption_style))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 5: HOW YOU CLEANED IT
    # ==========================================
    story.append(Paragraph("Section 5: How You Cleaned It (Decisions & clean(df) Execution)", h1_style))
    story.append(Paragraph(
        "We formulated rigorous data governance decisions for each anomaly and implemented the custom function <code>clean(df)</code>. "
        "The function adheres strictly to three data engineering invariants:<br/>"
        "1. <b>Non-destructive:</b> Operates on a defensive copy (<code>df.copy()</code>) without mutating original input.<br/>"
        "2. <b>Transparent Accounting:</b> Never drops rows silently; returns <code>(cleaned_df, dict{rule: rows_removed})</code>.<br/>"
        "3. <b>Fix vs. Drop:</b> Fixes valid records where possible (imputing <code>passenger_count = 0</code> to <code>1</code>) and drops fundamentally unrecoverable records.",
        body_style
    ))

    dec_img_path = "screenshots/step4_decisions.png"
    if os.path.exists(dec_img_path):
        story.append(Image(dec_img_path, width=530, height=125))
        story.append(Paragraph("<b>Evidence 5.1 (Step 4):</b> Decisions table specifying problem, action (drop/fix), rationale, and ownership.", code_caption_style))

    clean_img_path = "screenshots/step5_clean_metrics.png"
    if os.path.exists(clean_img_path):
        story.append(Image(clean_img_path, width=530, height=135))
        story.append(Paragraph("<b>Evidence 5.2 (Step 5):</b> Cleaning execution results: rows before (1,369,765), rows after (1,246,349), and rows removed per rule.", code_caption_style))

    story.append(Paragraph(
        "<b>Summary of Rows Removed:</b> The cleaning pipeline processed <b>1,369,765 initial rows</b>, removed <b>123,416 rows (9.01%)</b>, "
        "and retained <b>1,246,349 clean records</b>. Additionally, <b>26,246 rows</b> with zero passenger count were repaired via mode imputation without data loss.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 6: ANSWERS TO LAB QUESTIONS
    # ==========================================
    story.append(Paragraph("Section 6: Answers to Technical Questions", h1_style))

    story.append(Paragraph("<b>Q1: Why does the container reach the DB as pgdatabase, not localhost?</b>", h2_style))
    story.append(Paragraph(
        "Inside Docker, each container resides in its own isolated network namespace with its own private loopback interface (<code>localhost</code> / <code>127.0.0.1</code>). "
        "When code runs inside the python ingestion container, <code>localhost:5432</code> attempts to connect to a PostgreSQL daemon running inside the ingestion container itself, where no database exists (resulting in <code>Connection refused</code>). "
        "When containers are attached to a user-defined Docker bridge network (created by Docker Compose), Docker's embedded internal DNS server (running at <code>127.0.0.11</code>) automatically resolves the service name <code>pgdatabase</code> to the internal container IP assigned to the PostgreSQL instance. "
        "Therefore, containers communicate across the bridge network using service hostnames rather than localhost.",
        body_style
    ))

    story.append(Paragraph("<b>Q2: Why chunks, and what was wrong with replace for many months?</b>", h2_style))
    story.append(Paragraph(
        "<b>Part A (Why Chunks):</b> Loading massive datasets monolithically into RAM with <code>pd.read_csv()</code> creates severe memory spikes proportional to file size ($O(N)$). In constrained containerized environments, this triggers Out-Of-Memory (OOM) killer crashes. Chunks establish a constant streaming memory envelope ($O(K)$ where $K=100,000$), allowing files of arbitrary gigabyte sizes to be ingested safely.<br/>"
        "<b>Part B (What was wrong with replace for many months):</b> <code>df.to_sql(..., if_exists='replace')</code> drops and recreates the target database table from scratch on each invocation. If used across multiple monthly ingestion runs (e.g. January, February, March), each new month's run will completely destroy and wipe out the data from all preceding months! At the end of the year, only the December data would remain. The correct engineering pattern is to create the schema DDL on the first batch, followed by <code>if_exists='append'</code> for all subsequent chunks and months.",
        body_style
    ))

    story.append(Paragraph("<b>Q3: How did you verify your results?</b>", h2_style))
    story.append(Paragraph(
        "We verified our data profiling and cleaning through a multi-tier validation protocol:<br/>"
        "1. <b>Row Count Conservation Equation:</b> Mathematically verified: "
        "<code>Initial Rows (1,369,765) = Cleaned Rows (1,246,349) + Total Rows Removed (123,416)</code>.<br/>"
        "2. <b>Post-Cleaning Assertion Invariants:</b> Automated assertions confirmed in the cleaned DataFrame: "
        "<code>min(pickup_datetime) &gt;= '2021-01-01'</code> (0 violations), <code>(dropoff &lt; pickup).sum() == 0</code>, "
        "<code>(fare_amount &lt;= 0).sum() == 0</code>, <code>(trip_distance &lt;= 0).sum() == 0</code>, and <code>(passenger_count == 0).sum() == 0</code>.<br/>"
        "3. <b>DataFrame Immutability Check:</b> Verified that <code>id(df_cleaned) != id(df_raw)</code>, ensuring input dataframes were never mutated in-place.<br/>"
        "4. <b>Relational Database Verification:</b> Verified via <code>psql</code> that <code>SELECT COUNT(*) FROM yellow_taxi_trips;</code> matched expected chunk ingestion totals.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 7: WHAT BROKE (KEEP TOGETHER)
    # ==========================================
    sec7_elements = []
    sec7_elements.append(Paragraph("Section 7: What Broke (Error Encountered, Root Cause & Solution)", h1_style))
    sec7_elements.append(Paragraph(
        "<b>1. Error Hit:</b> <code>sys:1: DtypeWarning: Columns (6) have mixed types. Specify dtype option on import or set low_memory=False</code> followed by <code>ValueError: Cannot convert non-finite values (NA or inf) to integer</code>.<br/>"
        "<b>2. Cause:</b> When reading in chunks, chunks 1 through 12 contain complete integer values for <code>passenger_count</code> and <code>VendorID</code>. However, chunks 13 and 14 contain 98,352 null values (<code>NaN</code>). Legacy NumPy <code>int64</code> cannot represent nulls, forcing Pandas to either coerce integers into <code>float64</code> (e.g. <code>1.0</code>) or crash during downstream integer schema loading.<br/>"
        "<b>3. How We Fixed It:</b> We configured an explicit schema type dictionary using Pandas <code>Int64</code> nullable integer extension and <code>string</code> data types: "
        "<code>{'VendorID': 'Int64', 'passenger_count': 'Int64', 'RatecodeID': 'Int64', 'store_and_fwd_flag': 'string'}</code>. This enabled native integer parsing alongside <code>&lt;NA&gt;</code> without schema distortion or ingestion warnings.",
        body_style
    ))

    err_img_path = "screenshots/step7_error_and_fix.png"
    if os.path.exists(err_img_path):
        sec7_elements.append(Image(err_img_path, width=530, height=135))
        sec7_elements.append(Paragraph("<b>Evidence 7.1:</b> Error traceback showing mixed-type / NA integer failure and the applied Int64 schema fix.", code_caption_style))

    story.append(KeepTogether(sec7_elements))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Optimized PDF report generated successfully: {filename}")


if __name__ == "__main__":
    create_pdf_report()
