from flask import Flask, render_template, request, redirect, session
import json
import csv
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"

SONG_FILE = "songs.json"
SUGGESTIONS_FILE = "suggestions.json"

# ---------- Helpers ----------

def load_songs():
    with open(SONG_FILE, "r") as f:
        return json.load(f)

def save_songs(songs):
    with open(SONG_FILE, "w") as f:
        json.dump(songs, f, indent=2)

def sort_songs(songs, by="name"):
    return sorted(songs, key=lambda s: s.get(by, "").lower())

def load_suggestions():
    try:
        with open(SUGGESTIONS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_suggestions(suggestions):
    with open(SUGGESTIONS_FILE, "w") as f:
        json.dump(suggestions, f, indent=2)

# ---------- Routes ----------

@app.route("/")
def index():
    sort_by = request.args.get("sort", "name")
    songs = sort_songs(load_songs(), by=sort_by)
    return render_template("index.html", songs=songs)

@app.route("/songlist")
def songlist():
    sort_by = request.args.get("sort", "name")
    songs = sort_songs(load_songs(), by=sort_by)
    return render_template("song_list.html", songs=songs)

@app.route("/submit", methods=["POST"])
def submit():
    song_index = int(request.form["song_index"])
    name = request.form.get("name", "")
    tipped = request.form.get("tipped") == "true"

    songs = load_songs()
    song = songs[song_index]

    if not song["selected"]:
        song["selected"] = True
        song["tipped"] = tipped
        song["name_submitted"] = name
        song["timestamp"] = datetime.now().isoformat()
        songs = sort_songs(songs)
        save_songs(songs)

    return redirect("/")

@app.route("/queue")
def queue():
    songs = [s for s in load_songs() if s["selected"]]
    return render_template("queue.html", songs=songs)

@app.route("/suggestions")
def view_suggestions():
    suggestions = sorted(load_suggestions(), key=lambda s: s["text"].lower())
    return render_template("suggestions.html", suggestions=suggestions)

@app.route("/suggest", methods=["POST"])
def suggest():
    suggestion = request.form.get("suggestion", "").strip()
    if suggestion:
        suggestions = load_suggestions()
        suggestions.append({
            "text": suggestion,
            "timestamp": datetime.now().isoformat()
        })
        save_suggestions(suggestions)
    return redirect("/")

@app.route("/delete-suggestion", methods=["POST"])
def delete_suggestion():
    text = request.form.get("text", "").strip()
    suggestions = load_suggestions()
    suggestions = [s for s in suggestions if s["text"] != text]
    save_suggestions(suggestions)
    return redirect("/suggestions")

# ---------- Admin ----------

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pin = request.form.get("admin_pin", "").strip()
        if pin == "1999":
            session["admin_access"] = True
        else:
            session["admin_access"] = False
            return redirect("/admin")
    if request.method == "GET":
        pin = request.args.get("admin_pin", "").strip()
        if pin == "1999":
            session["admin_access"] = True

    if not session.get("admin_access"):
        return render_template("admin_login.html")
    return render_template("admin.html")

@app.route("/logout")
def logout():
    session.pop("admin_access", None)
    return redirect("/")

# ---------- Add Songs ----------

@app.route("/upload_csv", methods=["GET"])
def upload_csv_form():
    return render_template("upload_csv.html")

@app.route("/add_song", methods=["GET"])
def add_song_form():
    return render_template("add_song.html")


@app.route("/add-song", methods=["POST"])
def add_song():
    title = request.form.get("new_song", "").strip()
    artist = request.form.get("new_artist", "").strip()
    year = request.form.get("new_year", "").strip()

    if title and artist:
        new_song = {
            "name": title,
            "artist": artist,
            "year": year,
            "selected": False,
            "tipped": False,
            "name_submitted": "",
            "timestamp": ""
        }

        songs = load_songs()
        songs.append(new_song)
        songs = sort_songs(songs)
        save_songs(songs)

    return redirect("/admin")

@app.route("/upload-csv", methods=["POST"])
def upload_csv():
    file = request.files.get("csv_file")
    if not file:
        return redirect("/admin")

    filename = secure_filename(file.filename)
    if not filename.endswith(".csv"):
        return redirect("/admin")

    content = file.stream.read().decode("utf-8").splitlines()
    reader = csv.DictReader(content)

    preview = []
    for row in reader:
        title = row.get("name", "").strip()
        artist = row.get("artist", "").strip()
        year = row.get("year", "").strip()
        if title and artist:
            preview.append({
                "name": title,
                "artist": artist,
                "year": year
            })

    session["csv_preview"] = preview
    return render_template("csv_preview.html", preview=preview)

@app.route("/confirm-upload", methods=["POST"])
def confirm_upload():
    preview = session.pop("csv_preview", [])
    songs = load_songs()
    for row in preview:
        songs.append({
            "name": row["name"],
            "artist": row["artist"],
            "year": row["year"],
            "selected": False,
            "tipped": False,
            "name_submitted": "",
            "timestamp": ""
        })
    songs = sort_songs(songs)
    save_songs(songs)
    return redirect("/admin")

@app.route("/reset", methods=["POST"])
def reset():
    songs = load_songs()
    for song in songs:
        song["selected"] = False
        song["tipped"] = False
        song["name_submitted"] = ""
        song["timestamp"] = ""
    songs = sort_songs(songs)
    save_songs(songs)
    return redirect("/admin")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
