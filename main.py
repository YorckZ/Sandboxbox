from flask import Flask, render_template, request, jsonify
# from openai import OpenAI
# from dotenv import load_dotenv
# from flask import Flask, request, jsonify, render_template, redirect, url_for
# from werkzeug.utils import secure_filename
# import requests
# import json
import webbrowser
import threading
# import os
# import io
# import PyPDF2
# import sqlite3
import database.database_logic as db
import os
import requests
# from werkzeug.utils import secure_filename
# import PyPDF2
import graphviz
from flask import Response
from graphviz import Digraph


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
# try to import a PDF extractor
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

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

@app.route('/next_element', methods=['POST'])
def next_element():
    try:
        data = request.get_json()
        frage_id = data.get('frage_id')
        antwort = data.get('antwort')  # 'ja', 'nein', 'unsicher'

        # Get current question info
        frage = db.get_frage_by_id(frage_id)
        if not frage:
            return jsonify({"error": "Frage nicht gefunden"}), 404

        # # Map answer to the correct dict key (unsicher is lower-case in DB dict)
        # key_map = {'ja': 'Ja', 'nein': 'Nein', 'unsicher': 'unsicher'}
        # key = key_map.get(antwort)
        # if not key:
        #     return jsonify({"error": "Ungültige Antwort"}), 400

        # Determine the next element's ID based on the user's answer
        next_id = frage.get(antwort.capitalize())  # 'Ja', 'Nein', 'Unsicher' as column names
        # next_id = frage.get(key)

        if not next_id:
            # return jsonify({"done": True})  # End, or Absage/Zusage if you want
            return jsonify({"done": True, "message": "Keine weitere Frage. Fragebogen ist beendet."})

        # Now check: what type of element is next_id? (Frage, Antwort, Prompt)
        # Let's say you have a function like this:
        next_e = db.get_element_by_id(next_id)
        if not next_e:
            return jsonify({"error": "Element nicht gefunden"}), 404

        # next_element could contain the type (Frage, Antwort, Prompt) and relevant content
        return jsonify(next_e)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/graph")
def graph_page():
    # Simple page that embeds the SVG
    return render_template("graph.html")

@app.route("/graph.svg")
def graph_svg():
    data = db.get_all_elements_with_edges()

    dot = Digraph("SAT", format="svg")
    dot.attr(rankdir="LR", fontname="Helvetica")
    # make links open the whole page, not inside the <object>
    dot.attr('node', target="_top")

    shape_map = {1: "circle", 2: "box", 3: "triangle"}
    fill_map  = {1: "#E3F2FD", 2: "#E8F5E9", 3: "#FFF3E0"}

    BLUE   = "#1976D2"  # Initialfrage
    GREEN  = "#2E7D32"
    RED    = "#C62828"
    YELLOW = "#F9A825"

    # collect incoming targets and initial id
    incoming = set()
    for item in data:
        if item["TableID"] == 1:
            for tgt in (item["Ja"], item["Nein"], item["Unsicher"]):
                if tgt:
                    incoming.add(str(tgt))

    initial_eid = next((str(x["ElementID"]) for x in data
                        if x["TableID"] == 1 and x.get("Initial")), None)

    # NODES (CLICKABLE)
    for item in data:
        nid   = str(item["ElementID"])     # node id in graph
        t_id  = item["TableID"]            # 1=Frage, 2=Antwort, 3=Prompt
        fid   = str(item["ForeignID"])     # content id for editor routes
        label = item["Bez"] or f"ID {nid}"

        # Build edit URL per type (passes ?id=<content-id>)
        if t_id == 1:
            node_url = f"/edit_frage?id={fid}"
        elif t_id == 2:
            node_url = f"/edit_antwort?id={fid}"
        else:
            node_url = f"/edit_prompt?id={fid}"

        attrs = {
            "shape": shape_map.get(t_id, "ellipse"),
            "style": "filled",
            "fillcolor": fill_map.get(t_id, "#FFFFFF"),
            "URL": node_url,            # <-- makes the node clickable
            "tooltip": node_url,        # nice hover hint
        }

        # precedence: thick borders first
        locked = False
        if t_id == 1 and item.get("Initial"):
            attrs["color"] = BLUE
            attrs["penwidth"] = "3"
            locked = True
        elif nid not in incoming:
            attrs["color"] = RED
            attrs["penwidth"] = "3"
            locked = True

        # secondary styling (don’t overwrite thick ones)
        if not locked:
            if t_id in (2, 3):  # Antworten & Prompts
                if nid in incoming:
                    attrs["color"] = GREEN
                    attrs["penwidth"] = "1.5"
            elif t_id == 1:     # Fragen
                out_count = sum(1 for v in (item["Ja"], item["Nein"], item["Unsicher"]) if v)
                if out_count == 3:
                    attrs["color"] = GREEN
                    attrs["penwidth"] = "1.5"
                else:
                    attrs["color"] = YELLOW
                    attrs["penwidth"] = "1.5"

        dot.node(nid, label=label, **attrs)

    # EDGES
    for item in data:
        if item["TableID"] != 1:
            continue
        src = str(item["ElementID"])
        for edge_label, tgt in (("Ja", item["Ja"]), ("Nein", item["Nein"]), ("Unsicher", item["Unsicher"])):
            if tgt:
                dot.edge(src, str(tgt), label=edge_label)

    svg = dot.pipe(format="svg")
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "no-store"})




# </editor-fold>

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
        try:
            ja = int(data["ja"]) if data.get("ja") else None
        except Exception:
            ja = None
        try:
            nein = int(data["nein"]) if data.get("nein") else None
        except Exception:
            nein = None
        try:
            unsicher = int(data["unsicher"]) if data.get("unsicher") else None
        except Exception:
            unsicher = None
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

@app.route("/all_bez")
def all_bez():
    # fragen = db.get_all_fragen()
    # antworten = db.get_all_antworten()
    # prompts = db.get_all_prompts()
    #
    # # get all Bez, add table type and ID if you want (for lookup purposes)
    # bez_list = []
    # for row in fragen:
    #     bez_list.append({"Bez": row["Bez"], "type": "Frage", "ID": row["ID"]})
    # for row in antworten:
    #     bez_list.append({"Bez": row["Bez"], "type": "Antwort", "ID": row["ID"]})
    # for row in prompts:
    #     bez_list.append({"Bez": row["Bez"], "type": "Prompt", "ID": row["ID"]})

    # unified list with tbl_elemente.ID so flows work
    bez_list = db.get_all_bez_with_element_ids()

    # sort alphabetically by Bez
    bez_list.sort(key=lambda x: x["Bez"].lower())
    return jsonify(bez_list)

@app.route("/get_fragen", methods=["GET"])
def get_fragen():
    try:
        fragen = db.get_all_fragen()
        # return jsonify([{"ID": row[0], "Bez": row[1]} for row in fragen])
        return jsonify(fragen)  # already [{"ID":..., "Bez":...}]
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

@app.route("/get_initial_frage", methods=["GET"])
def get_initial_frage_route():
    frage = db.get_initial_frage()
    if frage:
        return jsonify(frage)
    return jsonify({"error": "Keine Initialfrage gefunden."}), 404

@app.route("/fragen_dropdown", methods=["GET"])
def fragen_dropdown():
    try:
        items = db.get_all_fragen_for_dropdown()
        return jsonify([{"id": it["ID"], "display": it["Display"]} for it in items])
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

        # Call database function to insert the answer
        db.create_antwort(bez, text)

        return jsonify({"message": "Antwort erfolgreich gespeichert!"})

    except ValueError:
        return jsonify({"message": "Fehler: Ungültige Eingabewerte!"}), 400
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route('/edit_antwort')
def edit_antwort():
    antworten = db.get_all_antworten()
    antworten_sorted = sorted(antworten, key=lambda x: x["Bez"])
    return render_template('_antwort_editieren.html', antworten=antworten_sorted)

@app.route("/get_antworten", methods=["GET"])
def get_antworten():
    try:
        antworten = db.get_all_antworten()
        return jsonify([{"ID": row["ID"], "Bez": row["Bez"]} for row in antworten])
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route("/get_antwort/<int:antwort_id>", methods=["GET"])
def get_antwort(antwort_id):
    try:
        antwort = db.get_antwort_by_id(antwort_id)
        if antwort:
            return jsonify(antwort)
        else:
            return jsonify({"message": "Antwort nicht gefunden"}), 404
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route("/update_antwort", methods=["POST"])
def update_antwort():
    try:
        data = request.get_json()

        antwort_id = data.get("id")
        bez = data.get("bez", "").strip()
        text = data.get("text", "").strip()

        if not antwort_id or not bez or not text:
            return jsonify({"message": "Fehlende erforderliche Felder!"}), 400

        db.update_antwort(antwort_id, bez, text)

        return jsonify({"message": "Antwort erfolgreich aktualisiert!"})
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

@app.route("/loeschen_antwort")
def delete_antwort_page():
    antworten = db.get_all_antworten()
    antworten_sorted = sorted(antworten, key=lambda x: x["Bez"])
    return render_template("_antwort_loeschen.html", antworten=antworten_sorted)

@app.route("/delete_antwort/<int:antwort_id>", methods=["DELETE"])
def delete_antwort(antwort_id):
    try:
        db.delete_antwort(antwort_id)
        return jsonify({"message": "Antwort erfolgreich gelöscht!"})
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
        # data = request.get_json()
        #
        # # Extract and sanitize input values
        # bez = data.get("bez")
        # system = data.get("system")
        # dsgvo = data.get("dsgvo", "")
        # task = data.get("task", "")
        #
        # # Call database function to insert the prompt
        # db.create_prompt(bez, system, dsgvo, task)

        data = request.get_json() or {}

        # Map frontend fields → DB fields
        bez = (data.get("bez") or "").strip()
        frage = (data.get("dropdown") or data.get("frage") or "").strip()
        dsgvo = data.get("c") or data.get("dsgvo") or ""

        if not bez:
            return jsonify({"ok": False, "message": "Kurzbezeichnung (bez) ist erforderlich!"}), 400

        db.create_prompt(bez=bez, frage=frage, dsgvo=dsgvo)

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
        # data = request.get_json()
        # if not data.get("id") or not data.get("bez") or not data.get("system"):
        #     return jsonify({"message": "Fehlende erforderliche Felder!"}), 400
        #
        # db.update_prompt(
        #     prompt_id=data["id"],
        #     bez=data["bez"],
        #     system=data["system"],
        #     dsgvo=data.get("dsgvo", ""),
        #     task=data.get("task", "")
        # )
        data = request.get_json() or {}

        prompt_id = data.get("id")
        if not prompt_id:
            return jsonify({"message": "ID fehlt."}), 400

        # Accept both old and new field names for a smoother transition
        bez = (data.get("bez") or "").strip()
        frage = (data.get("frage") or data.get("system") or data.get("dropdown") or "").strip()
        dsgvo = data.get("dsgvo") or data.get("c") or ""

        if not bez:
            return jsonify({"message": "Kurzbezeichnung (bez) ist erforderlich!"}), 400

        db.update_prompt(
            prompt_id=prompt_id,
            bez=bez,
            frage=frage,
            dsgvo=dsgvo
        )

        return jsonify({"message": "Prompt erfolgreich aktualisiert!"})
    except Exception as e:
        return jsonify({"message": f"Fehler: {str(e)}"}), 500

# @app.route('/run_prompt', methods=['POST'])
# def run_prompt():
#     try:
#         # Accept both JSON and multipart/form-data
#         prompt_id = None
#         user_input = ""
#         document_text = ""
#
#         if request.content_type and "application/json" in request.content_type:
#             data = request.get_json() or {}
#             prompt_id = data.get('prompt_id')
#             user_input = (data.get('user_input') or '').strip()
#             document_text = (data.get('document_text') or '').strip()
#             uploaded_file = None
#         else:
#             prompt_id = request.form.get('prompt_id')
#             user_input = (request.form.get('user_input') or '').strip()
#             document_text = (request.form.get('document_text') or '').strip()
#             uploaded_file = request.files.get('file')  # single PDF (optional)
#
#         if not prompt_id:
#             return jsonify({"error": "prompt_id fehlt"}), 400
#
#         prompt = db.get_prompt_by_id(int(prompt_id))
#         if not prompt:
#             return jsonify({"error": "Prompt nicht gefunden"}), 404
#
#         # Static label text (from your prompt templates)
#         preA = ("Du bist Experte für Datenschutz und sollst eine Empfehlung aussprechen. "
#                 "Dem Benutzer wurde folgende Frage gestellt:")
#         preB = "Der Nutzer ist sich nicht sicher. Der entsprechende Rechtstext lautet:"
#         instrF = ("Gib eine Empfehlung, ob die DSGVO zutrifft. Antworte zunächst nur mit Ja oder Nein. "
#                   "Anschließend begründe Deine Einschätzung. Zuletzt weise darauf hin, dass Du nur eine KI bist "
#                   "und dass dies keine Rechtsberatung darstellt.")
#
#         frage_str = prompt.get("Frage", "") or ""
#         dsgvo_str = prompt.get("DSGVO", "") or ""
#
#         parts = [
#             preA,
#             frage_str,
#             "",
#             preB,
#             dsgvo_str,
#             "",
#             f"Er hat hierzu folgendes angegeben: {user_input}" if user_input else "Es wurden keine zusätzlichen Angaben gemacht.",
#         ]
#
#         # If a file was provided, acknowledge it (plug in real PDF parsing later)
#         if uploaded_file and uploaded_file.filename:
#             parts.append(f"(Optional:) Weiterhin hat er folgende Dokumente bereitgestellt: {uploaded_file.filename}")
#         elif document_text:
#             parts.append("(Optional:)\nWeiterhin hat er folgende Dokumenteninhalte bereitgestellt: " + document_text)
#
#         parts.extend(["", instrF])
#         full_prompt = "\n".join(parts).strip()
#
#         # Demo output placeholder
#         demo_result = "⚠️ Demo: Hier würde jetzt die Antwort deines lokalen LLM erscheinen."
#
#         return jsonify({"prompt": full_prompt, "result": demo_result})
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

def _extract_pdf_text(file_storage) -> str:
    """Return plain text from the uploaded PDF (empty string if extraction fails)."""
    if not file_storage:
        return ""
    if PdfReader is None:
        # PyPDF2 not installed
        return ""
    try:
        # PyPDF2 can read from a file-like; use the stream directly
        reader = PdfReader(file_storage.stream)
        parts = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            parts.append(txt.strip())
        return "\n\n".join([p for p in parts if p])
    except Exception:
        return ""

def _frage_text_only(frage_field: str) -> str:
    """Input is 'Bez: Text' (or just Text). Return only the Text part."""
    if not frage_field:
        return ""
    if ":" in frage_field:
        return frage_field.split(":", 1)[1].strip()
    return frage_field.strip()

@app.route('/run_prompt', methods=['POST'])
def run_prompt():
    """
    Compose the final prompt (without showing it), send it to a local Ollama model,
    return only the model's response.
    """
    try:
        # Accept JSON and multipart/form-data
        content_type = (request.content_type or "")
        if "application/json" in content_type:
            data = request.get_json() or {}
            prompt_id = data.get('prompt_id')
            user_input = (data.get('user_input') or '').strip()
            document_text = (data.get('document_text') or '').strip()
            uploaded_file = None
        else:
            prompt_id = request.form.get('prompt_id')
            user_input = (request.form.get('user_input') or '').strip()
            document_text = (request.form.get('document_text') or '').strip()
            uploaded_file = request.files.get('file')

        if not prompt_id:
            return jsonify({"error": "prompt_id fehlt"}), 400

        prompt = db.get_prompt_by_id(int(prompt_id))
        if not prompt:
            return jsonify({"error": "Prompt nicht gefunden"}), 404

        # A/B/F fixed parts
        pre_a = ("Du bist Experte für Datenschutz und sollst eine Empfehlung aussprechen. "
                "Dem Benutzer wurde folgende Frage gestellt:")
        pre_b = "Der Nutzer ist sich nicht sicher. Der entsprechende Rechtstext lautet:"
        instr_f = ("Gib eine Empfehlung, ob die DSGVO zutrifft. Antworte zunächst nur mit Ja oder Nein. "
                  "Anschließend begründe Deine Einschätzung. Zuletzt weise darauf hin, dass Du nur eine KI bist "
                  "und dass dies keine Rechtsberatung darstellt.")

        frage_text = _frage_text_only(prompt.get("Frage", "") or "")
        dsgvo_str = prompt.get("DSGVO", "") or ""

        # Extract PDF text (if any) and combine with optional document_text field
        pdf_text = _extract_pdf_text(uploaded_file)
        extra_doc = document_text.strip()
        combined_doc_text = "\n\n".join([t for t in [pdf_text, extra_doc] if t]).strip()

        # Build the final user prompt (not returned to client)
        parts = [
            pre_a,
            frage_text,
            "",
            pre_b,
            dsgvo_str,
            "",
            f"Er hat hierzu folgendes angegeben: {user_input}" if user_input else "Es wurden keine zusätzlichen Angaben gemacht.",
        ]
        if combined_doc_text:
            parts.append("(Optional:) Weiterhin hat er folgende Dokumenteninhalte bereitgestellt:\n" + combined_doc_text)
        parts.extend(["", instr_f])
        full_prompt = "\n".join(parts).strip()

        # Call local Ollama
        model_name = os.getenv("OLLAMA_MODEL", "llama3.1")  # set OLLAMA_MODEL in your env if you prefer
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=120
            )
            r.raise_for_status()
            data = r.json()
            answer = (data.get("response") or "").strip()
            if not answer:
                return jsonify({"error": "Leere Antwort vom LLM."}), 502
            return jsonify({"result": answer})
        except requests.RequestException as re:
            return jsonify({"error": f"Ollama nicht erreichbar oder Fehler: {re}"}), 502

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/loeschen_prompt')
def loeschen_prompt():
    prompts = db.get_all_prompts()
    return render_template('_prompt_loeschen.html', prompts=prompts)

@app.route("/delete_prompt/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    # try:
    #     db.delete_prompt(prompt_id)
    #     return jsonify({"message": "Prompt erfolgreich gelöscht!"})
    # except Exception as e:
    #     return jsonify({"message": f"Fehler: {str(e)}"}), 500
    try:
        if db.prompt_is_referenced(prompt_id):
            return jsonify({"message": "Prompt wird noch von Fragen referenziert und kann nicht gelöscht werden."}), 400
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
