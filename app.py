from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import uuid
import os

app = Flask(__name__)

# ---------- CONFIG ----------
OUTPUT_DIR = "quotations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

THEME = {
    "title": colors.HexColor("#8B0000"),
    "header_bg": colors.HexColor("#E6E6E6"),
    "header_text": colors.HexColor("#001667"),
    "table_border": colors.black,
    "price_text": colors.HexColor("#8B0000"),
    "normal_text": colors.HexColor("#001667"),
    "notes_text": colors.HexColor("#001667"),
    "footer_text": colors.HexColor("#001667")
}

# ---------- PDF GENERATOR ----------
def generate_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Letterhead
    c.drawImage("static/letterhead.jpg", 1*cm, height-6*cm, width=18*cm, height=5*cm)

    # Date
    today = datetime.now().strftime("%d-%m-%Y")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(THEME["table_border"])
    c.drawRightString(width-2*cm, height-6.5*cm, f"Date : {today}")

    y = height - 7.5*cm

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(THEME["title"])
    c.drawCentredString(width/2, y, "Quotation For Employee Transport Service")
    y -= 2*cm

    # TO section
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(THEME["normal_text"])
    c.drawString(2*cm, y, "TO,")
    y -= 0.7*cm
    c.drawString(2*cm, y, data["to_company"])
    y -= 0.7*cm
    c.drawString(2*cm, y, data["to_location"])
    y -= 1.5*cm

    # ---------- TABLE ----------
    headers = data["headers"]
    rows = data["rows"]

    table_x = 2*cm
    table_w = 17*cm
    row_h = 0.8*cm

    # Column width ratios (first wide, last narrow)
    col_ratios = [0.40, 0.25, 0.20, 0.15]
    col_widths = [table_w * r for r in col_ratios]

    col_x = [table_x]
    for w in col_widths[:-1]:
        col_x.append(col_x[-1] + w)

    top_y = y
    total_rows = 1 + len(rows)
    table_h = total_rows * row_h

    # ----- BORDERS FIRST (IMPORTANT) -----
    c.setStrokeColor(THEME["table_border"])
    c.setLineWidth(1)
    c.rect(table_x, top_y - table_h, table_w, table_h)

    for i in range(1, total_rows):
        c.line(table_x, top_y - i*row_h, table_x + table_w, top_y - i*row_h)

    x_pos = table_x
    for w in col_widths[:-1]:
        x_pos += w
        c.line(x_pos, top_y, x_pos, top_y - table_h)

    # ----- HEADER BACKGROUND -----
    # c.setFillColor(THEME["header_bg"])
    # c.rect(table_x, top_y - row_h, table_w, row_h, fill=1, stroke=0)

    # ----- HEADER TEXT (LAST LAYER) -----
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(THEME["header_text"])
    header_y = top_y - 0.65*cm

    for i, header in enumerate(headers):
        c.drawString(col_x[i] + 0.2*cm, header_y, header)

    # ----- TABLE ROWS -----
    c.setFont("Helvetica-Bold", 12)
    text_y = top_y - row_h

    for row in rows:
        text_y -= row_h
        for i, cell in enumerate(row):
            if i == 0:
                c.setFillColor(THEME["price_text"])
            else:
                c.setFillColor(THEME["price_text"])
            c.drawString(col_x[i] + 0.2*cm, text_y + 0.3*cm, str(cell))

    y = top_y - table_h - 1*cm

    # ---------- NOTES ----------
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(THEME["notes_text"])
    for note in data["notes"]:
        c.drawString(2*cm, y, f"• {note}")
        y -= 0.6*cm

    # ---------- FOOTER ----------
    y -= 1*cm
    c.setFillColor(THEME["footer_text"])
    c.drawString(2*cm, y, "JAGTAP TRAVELS GST NO - 27AKGPJ1825N1ZX")
    y -= 0.6*cm
    c.drawString(2*cm, y, "BANK - AXIS BANK | BRANCH - SASWAD")
    y -= 0.6*cm
    c.drawString(2*cm, y, "ACCOUNT NO - 916020073533410")
    y -= 0.6*cm
    c.drawString(2*cm, y, "IFS CODE - UTIB0002985")

    # Stamp & Signature
    c.drawImage("static/stamp.png", width-7*cm, 1.5*cm, width=5*cm, height=4*cm, mask="auto")

    c.save()

# ---------- ROUTE ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        raw_headers = request.form.getlist("headers[]")
        headers = [h.strip().upper() for h in raw_headers if h.strip()]

        # Safety fallback
        if len(headers) != 4:
            headers = [
                "TYPE OF VEHICLE",
                "10 HOURS 80 KM",
                "EXTRA HOURS",
                "EXTRA KM"
            ]

        vehicles = request.form.getlist("vehicle[]")
        rate1 = request.form.getlist("rate1[]")
        rate2 = request.form.getlist("rate2[]")
        rate3 = request.form.getlist("rate3[]")

        rows = []
        for i in range(len(vehicles)):
            rows.append([
                vehicles[i],
                rate1[i],
                rate2[i],
                rate3[i]
            ])

        notes = [n for n in request.form.getlist("notes[]") if n.strip()]

        data = {
            "to_company": request.form["to_company"],
            "to_location": request.form["to_location"],
            "headers": headers,
            "rows": rows,
            "notes": notes
        }

        filename = f"{OUTPUT_DIR}/quotation_{uuid.uuid4().hex}.pdf"
        generate_pdf(data, filename)

        return send_file(filename, as_attachment=True)

    return render_template("index.html")

# ---------- RUN ----------
if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=True) # for developement
    app.run()

