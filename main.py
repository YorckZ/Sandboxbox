from flask import Flask, render_template, request, jsonify
# from openai import OpenAI
# from dotenv import load_dotenv
# from flask import Flask, request, jsonify, render_template, redirect, url_for
# from werkzeug.utils import secure_filename
# import requests
# import json
import webbrowser
import threading
import os
# import io
# import PyPDF2
# import sqlite3
import database.database_logic as db


# <editor-fold desc="Basic code functionality">
app = Flask(__name__)
# UPLOAD_FOLDER = 'uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
#
# if not api_key:
#     raise ValueError("API key not found. Please make sure OPENAI_API_KEY is set in the .env file.")
#
# client = OpenAI(api_key=api_key)
db.init_db()
# </editor-fold>

@app.route('/')
def home():
    # Main Page
    return render_template('index.html')

@app.route('/sat')
def sat():
    # Self-Assessment Tool Page (old style)
    return render_template('dynamic.html')

@app.route('/new')
def new():
    # Self-Assessment Tool Page (new style)
    return render_template('new.html')

# ===========================================================================================================

# <editor-fold desc="Fragen">

@app.route('/anlegen_frage')
def anlegen_frage():
    return render_template('_frage_anlegen.html')

@app.route('/save_frage', methods=['POST'])
def save_frage():
    try:
        data = request.get_json()

        # Extract and sanitize input values
        bez = data.get("bez", "").strip()
        text = data.get("text", "").strip()
        bem = data.get("bem", "").strip() if data.get("bem") else None
        ja = int(data["ja"]) if data.get("ja") else None
        nein = int(data["nein"]) if data.get("nein") else None
        unsicher = int(data["unsicher"]) if data.get("unsicher") else None
        initial = bool(int(data.get("initial", 0)))  # Convert "0"/"1" to boolean

        # Call database function to insert the question
        db.create_frage(bez, text, bem, ja, nein, unsicher, initial)

        return jsonify({"message": "Frage erfolgreich gespeichert!"})

    except ValueError:
        return jsonify({"message": "Fehler: Ungültige Eingabewerte!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route('/edit_frage')
def edit_frage():
    fragen = db.get_all_fragen()
    fragen_sorted = sorted(fragen, key=lambda x: x["Bez"])
    return render_template('_frage_editieren.html', fragen=fragen_sorted)

@app.route("/get_fragen", methods=["GET"])
def get_fragen():
    try:
        fragen = db.get_all_fragen()
        return jsonify([{"ID": row[0], "Bez": row[1]} for row in fragen])
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route("/get_frage/<int:frage_id>", methods=["GET"])
def get_frage(frage_id):
    try:
        frage = db.get_frage_by_id(frage_id)
        if frage:
            return jsonify(frage)
        else:
            return jsonify({"message": "Frage nicht gefunden"}), 404
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route("/update_frage", methods=["POST"])
def update_frage():
    try:
        data = request.get_json()

        frage_id = data.get("id")
        bez = data.get("bez")
        text = data.get("text")
        bem = data.get("bem", "")
        ja = int(data["ja"]) if data.get("ja") else None
        nein = int(data["nein"]) if data.get("nein") else None
        unsicher = int(data["unsicher"]) if data.get("unsicher") else None
        initial = bool(int(data.get("initial", 0)))

        if not frage_id or not bez or not text:
            return jsonify({"message": "Fehlende erforderliche Felder!"}), 400

        db.update_frage(frage_id, bez, text, bem, ja, nein, unsicher, initial)

        return jsonify({"message": "Frage erfolgreich aktualisiert!"})
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route("/loeschen_frage")
def delete_frage_page():
    fragen = db.get_all_fragen()
    fragen_sorted = sorted(fragen, key=lambda x: x["Bez"])
    return render_template("_frage_loeschen.html", fragen=fragen_sorted)

@app.route("/delete_frage/<int:frage_id>", methods=["DELETE"])
def delete_frage(frage_id):
    try:
        db.delete_frage(frage_id)
        return jsonify({"message": "Frage erfolgreich gelöscht!"})
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

# </editor-fold>

# ===========================================================================================================

# <editor-fold desc="Antworten">
@app.route('/anlegen_antwort')
def anlegen_antwort():
    return render_template('_antwort_anlegen.html')


@app.route('/save_antwort', methods=['POST'])
def save_antwort():
    try:
        data = request.get_json()

        # Extract and sanitize input values
        bez = data.get("bez", "").strip()
        text = data.get("text", "").strip()

        # Call database function to insert the question
        db.create_antwort(bez, text)

        return jsonify({"message": "Ergebnis erfolgreich gespeichert!"})

    except ValueError:
        return jsonify({"message": "Fehler: Ungültige Eingabewerte!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500
# </editor-fold>

# ===========================================================================================================

# <editor-fold desc="Prompts">

@app.route('/anlegen_prompt')
def anlegen_prompt():
    return render_template('_prompt_anlegen.html')

@app.route('/save_prompt', methods=['POST'])
def save_prompt():
    try:
        data = request.get_json()

        # Extract and sanitize input values
        bez = data.get("bez")
        system = data.get("system")
        dsgvo = data.get("dsgvo", "")
        task = data.get("task", "")

        # Call database function to insert the prompt
        db.create_prompt(bez, system, dsgvo, task)

        return jsonify({"message": "Prompt saved successfully!"})

    except ValueError:
        return jsonify({"message": "Fehlende erforderliche Felder!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route('/edit_prompt')
def edit_prompt():
    return render_template('_prompt_editieren.html')

@app.route("/get_prompts", methods=["GET"])
def get_prompts():
    return jsonify(db.get_all_prompts())

@app.route("/get_prompt/<int:prompt_id>", methods=["GET"])
def get_prompt(prompt_id):
    prompt = db.get_prompt_by_id(prompt_id)
    if prompt:
        return jsonify(prompt)
    return jsonify({"message": "Prompt nicht gefunden"}), 404

@app.route("/update_prompt", methods=["POST"])
def update_prompt():
    try:
        data = request.get_json()
        if not data.get("id") or not data.get("bez") or not data.get("system"):
            return jsonify({"message": "Fehlende erforderliche Felder!"}), 400

        db.update_prompt(
            prompt_id=data["id"],
            bez=data["bez"],
            system=data["system"],
            dsgvo=data.get("dsgvo", ""),
            task=data.get("task", "")
        )
        return jsonify({"message": "Prompt erfolgreich aktualisiert!"})
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route('/loeschen_prompt')
def loeschen_prompt():
    prompts = db.get_all_prompts()
    return render_template('_prompt_loeschen.html', prompts=prompts)

@app.route("/delete_prompt/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    try:
        db.delete_prompt(prompt_id)
        return jsonify({"message": "Prompt erfolgreich gelöscht!"})
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500


# </editor-fold>

# ===========================================================================================================

def open_browser():
    # required to automatically start the browser once the webserver is running
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == '__main__':
    # print(app.url_map)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()

    app.run(debug=True)
