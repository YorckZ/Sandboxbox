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


@app.route('/insert_prompt')
def insert_prompt():
    return render_template('insert_prompt.html')


@app.route('/save_prompt', methods=['POST'])
def save_prompt():
    data = request.get_json()
    text = data.get("text", "").strip()

    if text:
        db.insert_into_tbl_prompts(text)
        return jsonify({"message": "Prompt saved successfully!"})
    else:
        return jsonify({"message": "Input cannot be empty!"}), 400


@app.route('/insert_frage')
def insert_frage():
    return render_template('insert_frage.html')


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


# @app.route('/edit_frage')
# def edit_frage():
#     return render_template('edit_frage.html')


def open_browser():
    # required to automatically start the browser once the webserver is running
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == '__main__':
    # print(app.url_map)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()

    app.run(debug=True)
