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
import sqlite3
import database.database_logic as db


# <editor-fold desc="Basic code functionality">
app = Flask(__name__)
# UPLOAD_FOLDER = 'uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("API key not found. Please make sure OPENAI_API_KEY is set in the .env file.")
# client = OpenAI(api_key=api_key)
db.init_db()
# </editor-fold>


@app.route('/')
def home():
    # Main Page
    return render_template('index.html')


@app.route('/sat')
def sat():
    # Self-Assessment Tool Page
    return render_template('dynamic.html')


@app.route('/new')
def new():
    # Self-Assessment Tool Page
    return render_template('new.html')


@app.route('/anlegen_frage')
def anlegen_frage():
    return render_template('anlegen_frage.html')


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
        db.insert_into_tbl_fragen(bez, text, bem, ja, nein, unsicher, initial)

        return jsonify({"message": "Frage erfolgreich gespeichert!"})

    except ValueError:
        return jsonify({"message": "Fehler: Ungültige Eingabewerte!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500


@app.route('/anlegen_antwort')
def anlegen_antwort():
    return render_template('anlegen_antwort.html')


@app.route('/save_antwort', methods=['POST'])
def save_antwort():
    try:
        data = request.get_json()

        # Extract and sanitize input values
        bez = data.get("bez", "").strip()
        text = data.get("text", "").strip()

        # Call database function to insert the question
        db.insert_into_tbl_antworten(bez, text)

        return jsonify({"message": "Ergebnis erfolgreich gespeichert!"})

    except ValueError:
        return jsonify({"message": "Fehler: Ungültige Eingabewerte!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500


# <editor-fold desc="Prompts">
@app.route('/anlegen_prompt')
def anlegen_prompt():
    return render_template('anlegen_prompt.html')


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
        db.insert_into_tbl_prompts(bez, system, dsgvo, task)

        return jsonify({"message": "Prompt saved successfully!"})

    except ValueError:
        return jsonify({"message": "Fehlende erforderliche Felder!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500


@app.route('/edit_prompt')
def edit_prompt():
    return render_template('edit_prompt.html')


@app.route("/get_prompts", methods=["GET"])
def get_prompts():
    conn, cursor = db.open_connection()
    cursor.execute("SELECT ID, Bez FROM tbl_prompts")
    prompts = cursor.fetchall()
    db.close_connection(conn)
    return jsonify([{"ID": row[0], "Bez": row[1]} for row in prompts])


@app.route("/get_prompt/<int:prompt_id>", methods=["GET"])
def get_prompt(prompt_id):
    conn, cursor = db.open_connection()
    cursor.execute("SELECT Bez, System, DSGVO, Task FROM tbl_prompts WHERE ID = ?", (prompt_id,))
    prompt = cursor.fetchone()
    db.close_connection(conn)

    if prompt:
        return jsonify({
            "Bez": prompt[0],
            "System": prompt[1],
            "DSGVO": prompt[2],
            "Task": prompt[3]
        })
    else:
        return jsonify({"message": "Prompt nicht gefunden"}), 404


@app.route("/update_prompt", methods=["POST"])
def update_prompt():
    data = request.get_json()

    prompt_id = data.get("id")
    bez = data.get("bez")
    system = data.get("system")
    dsgvo = data.get("dsgvo", "")
    task = data.get("task", "")

    if not prompt_id or not bez or not system:
        return jsonify({"message": "Fehlende erforderliche Felder!"}), 400

    conn, cursor = db.open_connection()

    cursor.execute("""
        UPDATE tbl_prompts
        SET Bez = ?, System = ?, DSGVO = ?, Task = ?
        WHERE ID = ?
    """, (bez, system, dsgvo, task, prompt_id))

    conn.commit()
    db.close_connection(conn)

    return jsonify({"message": "Prompt erfolgreich aktualisiert!"})
# </editor-fold>


def open_browser():
    # required to automatically start the browser once the webserver is running
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == '__main__':
    # print(app.url_map)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()

    app.run(debug=True)
