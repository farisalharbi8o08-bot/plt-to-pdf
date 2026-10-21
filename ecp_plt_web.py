"""Run a local website for converting ECP Executive .plt files to PDF."""
from io import BytesIO
from pathlib import Path
import tempfile

from flask import Flask, render_template_string, request, send_file

from ecp_plt_to_pdf import main as convert_to_pdf


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ME465 Lab Graphs</title>
</head>
<body>
  <h1>ME465 Lab Graphs</h1>
  <p>Choose an ECP Executive .plt file to create and download a PDF plot.</p>
  {% if error %}<p role="alert">{{ error }}</p>{% endif %}
  <form method="post" enctype="multipart/form-data">
    <input type="file" name="plt_file" accept=".plt" required>
    <button type="submit">Convert and download PDF</button>
  </form>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(PAGE, error=None)

    uploaded_file = request.files.get("plt_file")
    if uploaded_file is None or not uploaded_file.filename:
        return render_template_string(PAGE, error="Choose a .plt file to convert."), 400

    filename = Path(uploaded_file.filename)
    if filename.suffix.lower() != ".plt":
        return render_template_string(PAGE, error="The selected file must have a .plt extension."), 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.plt"
            output_path = Path(temp_dir) / "output.pdf"
            uploaded_file.save(input_path)
            convert_to_pdf(input_path, output_path)
            pdf_data = output_path.read_bytes()
    except (AssertionError, OSError, ValueError) as exc:
        return render_template_string(PAGE, error=f"Could not convert this file: {exc}"), 400

    return send_file(
        BytesIO(pdf_data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{filename.stem}.pdf",
    )


@app.errorhandler(413)
def request_too_large(_error):
    return render_template_string(
        PAGE,
        error="The uploaded file is too large. The limit is 10 MB.",
    ), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
