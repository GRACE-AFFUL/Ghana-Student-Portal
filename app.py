"""
Students' Portal — Fullstack Python capstone project (Ghana edition).

A Flask application where students submit their personal and academic
details. Records go into a SQLite database; the uploaded photo is saved to
disk with only its filename stored in the DB. The Region of Origin and
District select boxes are populated asynchronously from Ghana's 16
administrative regions and their 261 districts (MMDAs), with the District
options depending on the chosen Region.

Run it with:   python app.py
Then open:      http://127.0.0.1:5000
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, abort,
)
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "portal.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
REGIONS_FILE = os.path.join(BASE_DIR, "static", "data", "regions.json")

# Which image types we accept for the student photo.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload cap

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-only")  # needed for flash()
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    """Open a new SQLite connection with row access by column name."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # rows behave like dicts
    return connection


def init_db():
    """Create the students table on first run if it does not exist yet."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name        TEXT    NOT NULL,
                middle_name       TEXT,
                last_name         TEXT    NOT NULL,
                email             TEXT    NOT NULL,
                date_of_birth     TEXT    NOT NULL,
                gender            TEXT    NOT NULL,
                phone             TEXT    NOT NULL,
                address           TEXT    NOT NULL,
                region            TEXT    NOT NULL,
                district          TEXT    NOT NULL,
                next_of_kin       TEXT    NOT NULL,
                wassce_aggregate  INTEGER NOT NULL,
                image_filename    TEXT    NOT NULL,
                admission_status  TEXT    NOT NULL DEFAULT 'Pending',
                created_at        TEXT    NOT NULL
            )
            """
        )


def load_regions():
    """
    Read the regions data file once per request that needs it.

    The file is an array of objects (same shape as the course's data file):
        [ { "region": "Greater Accra", "districts": [ ... ] }, ... ]
    """
    with open(REGIONS_FILE, encoding="utf-8") as f:
        return json.load(f)


# Create the table as soon as the app is imported, so the app also works
# when started with `flask run` instead of `python app.py`.
init_db()


# --------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------
def allowed_file(filename):
    """Return True if the filename has a permitted image extension."""
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(image):
    """
    Save an uploaded photo to the uploads folder with a unique, safe name.
    Returns the stored filename (which is what goes in the database).
    """
    safe_name = secure_filename(image.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    image.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
    return unique_name


# The exact fields the form must send. Used to validate that nothing is blank.
REQUIRED_FIELDS = [
    "first_name", "last_name", "email", "date_of_birth", "gender",
    "phone", "address", "region", "district", "next_of_kin",
    "wassce_aggregate",
]


# --------------------------------------------------------------------------
# Page routes
# --------------------------------------------------------------------------
@app.route("/")
def landing():
    """Landing page: intro + call-to-action button that leads to the form."""
    return render_template("index.html")


@app.route("/form")
def form():
    """The portal form where a student enters all of their details."""
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    """
    Handle the submitted portal form.

    Steps:
      1. Validate every required text field is filled.
      2. Validate an image was chosen and has an allowed type.
      3. Save the image to /static/uploads with a unique name.
      4. Insert the student's details (image *name* only) into the DB.
      5. Redirect to the students index on success, or back to the form.
    """
    # 1. Check that all text/select/radio fields are present and non-empty.
    missing = [f for f in REQUIRED_FIELDS if not request.form.get(f, "").strip()]
    if missing:
        flash("Please fill in every field before submitting.", "error")
        return redirect(url_for("form"))

    # 2. Validate the uploaded image.
    image = request.files.get("photo")
    if image is None or image.filename == "":
        flash("Please choose a photo to upload.", "error")
        return redirect(url_for("form"))
    if not allowed_file(image.filename):
        flash("Photo must be a PNG, JPG, GIF or WEBP image.", "error")
        return redirect(url_for("form"))

    # Extra server-side checks (the browser checks can be bypassed).
    try:
        aggregate = int(request.form["wassce_aggregate"])
    except ValueError:
        aggregate = 0
    if not 6 <= aggregate <= 54:
        flash("WASSCE aggregate must be a number from 6 to 54.", "error")
        return redirect(url_for("form"))

    region = request.form["region"].strip()
    district = request.form["district"].strip()
    valid_districts = next(
        (r["districts"] for r in load_regions() if r["region"] == region), []
    )
    if district not in valid_districts:
        flash("Please choose a valid region and district.", "error")
        return redirect(url_for("form"))

    # 3. Save the file; keep only its name for the database.
    stored_filename = save_photo(image)

    # 4. Insert the record. Notice we store the image *filename*, not the file.
    try:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO students (
                    first_name, middle_name, last_name, email, date_of_birth,
                    gender, phone, address, region, district, next_of_kin,
                    wassce_aggregate, image_filename, admission_status,
                    created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request.form["first_name"].strip(),
                    request.form.get("middle_name", "").strip(),
                    request.form["last_name"].strip(),
                    request.form["email"].strip(),
                    request.form["date_of_birth"].strip(),
                    request.form["gender"].strip(),
                    request.form["phone"].strip(),
                    request.form["address"].strip(),
                    region,
                    district,
                    request.form["next_of_kin"].strip(),
                    aggregate,
                    stored_filename,
                    "Pending",
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
    except sqlite3.Error:
        # On failure remove the orphaned photo and send the user back.
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], stored_filename))
        except OSError:
            pass
        flash("Something went wrong saving your details. Please try again.", "error")
        return redirect(url_for("form"))

    # 5. Success -> go to the students index page.
    flash("Your details were submitted successfully.", "success")
    return redirect(url_for("students"))


@app.route("/students")
def students():
    """Index page: a table listing every student in the database."""
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()
    return render_template("students.html", students=rows)


@app.route("/student/<int:student_id>")
def student_details(student_id):
    """Details page: the full record for one student."""
    with get_db() as db:
        student = db.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()
    if student is None:
        abort(404)
    return render_template("details.html", student=student)


# --------------------------------------------------------------------------
# JSON API routes (called asynchronously by JavaScript)
# --------------------------------------------------------------------------
@app.route("/api/regions")
def api_regions():
    """Return the list of region names (for the first select box)."""
    regions = load_regions()
    return jsonify([r["region"] for r in regions])


@app.route("/api/districts/<region>")
def api_districts(region):
    """Return the districts for the chosen region (dependent select box)."""
    for entry in load_regions():
        if entry["region"].lower() == region.lower():
            return jsonify(entry["districts"])
    return jsonify([])  # unknown region -> empty list


@app.route("/api/student/<int:student_id>/status", methods=["POST"])
def api_update_status(student_id):
    """
    Update a student's admission status asynchronously.

    The details page sends the new status here with fetch(); we save it and
    reply with JSON so the page can update without reloading.
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()
    valid = {"Pending", "Admitted", "Rejected"}
    if new_status not in valid:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    with get_db() as db:
        cursor = db.execute(
            "UPDATE students SET admission_status = ? WHERE id = ?",
            (new_status, student_id),
        )
    if cursor.rowcount == 0:
        return jsonify({"ok": False, "error": "Student not found"}), 404
    return jsonify({"ok": True, "status": new_status})


# --------------------------------------------------------------------------
# Template helpers
# --------------------------------------------------------------------------
@app.context_processor
def inject_year():
    """Make the current year available to every template (for the footer)."""
    return {"current_year": datetime.now().year}


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True is for local development only; turn it off before deploying.
    app.run(debug=False)
