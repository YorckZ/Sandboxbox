from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import requests
import json
import webbrowser
import threading
import os
import io
import PyPDF2
import sqlite3


def init_db():
    # SQLite DB
    with sqlite3.connect("database/database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT NOT NULL
            )
        """)
        conn.commit()


# <editor-fold desc="Basic code functionality">
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please make sure OPENAI_API_KEY is set in the .env file.")
client = OpenAI(api_key=api_key)
init_db()
# </editor-fold>


@app.route('/')
def home():
    # Main Page
    return render_template('index.html')


@app.route('/sat')
def sat():
    # Self-Assessment Tool Page
    return render_template('dynamic.html')


@app.route('/analyze_chatgpt', methods=['POST'])
def analyze_chatgpt():
    # prompt = f'''Du bist Experte für Datenschutz und sollst eine Empfehlung aussprechen. Der Benutzer wurde gefragt, ob
    # sein Unternehmen personenbezogene Daten im Sinne des Art. 4 Nr. 1, 2 der DSGVO verarbeitet. Der Nutzer ist sich
    # nicht sicher. Der entsprechende Rechtstext lautet: {paragraph}.
    # Er hat hierzu folgendes angegeben: {notes}.
    # Weiterhin hat er folgende Dokumenteninhalte bereitgestellt: {document_text}.
    # Gib eine Empfehlung, ob die DSGVO zutrifft. Antworte zunächst nur mit Ja oder Nein. Anschließend begründe Deine
    # Einschätzung. Zuletzt weise darauf hin, dass Du nur eine KI bist und dies keine Rechtsberatung darstellt.'''

    # ChatGPT chat + PDF file content
    notes = request.form.get('prompt', '')
    file = request.files.get('file')
    paragraph = '''Im Sinne dieser Verordnung bezeichnet der Ausdruck: „personenbezogene Daten“ alle Informationen, die
     sich auf eine identifizierte oder identifizierbare natürliche Person (im Folgenden „betroffene Person“) beziehen; 
     als identifizierbar wird eine natürliche Person angesehen, die direkt oder indirekt, insbesondere mittels Zuordnung 
     zu einer Kennung wie einem Namen, zu einer Kennnummer, zu Standortdaten, zu einer Online-Kennung oder zu einem oder 
     mehreren besonderen Merkmalen, die Ausdruck der physischen, physiologischen, genetischen, psychischen, wirtschaftlichen, 
     kulturellen oder sozialen Identität dieser natürlichen Person sind, identifiziert werden kann.'''

    if not notes:
        return jsonify({'error': 'Prompt is required'}), 400

    prompt = f'''Du bist Experte für Datenschutz und sollst eine Empfehlung aussprechen. Der Benutzer wurde gefragt, ob
    sein Unternehmen personenbezogene Daten im Sinne des Art. 4 Nr. 1, 2 der DSGVO verarbeitet. Der Nutzer ist sich
    nicht sicher. Der entsprechende Rechtstext lautet: {paragraph}.
    Er hat hierzu folgendes angegeben: {notes}.'''

    try:
        if file and file.filename.endswith('.pdf'):
            pdf_file = io.BytesIO(file.read())
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            document_text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
            prompt += f'''Weiterhin hat er folgende Dokumenteninhalte bereitgestellt: {document_text}.'''

        prompt += '''Gib eine Empfehlung, ob die DSGVO zutrifft. Antworte zunächst nur mit Ja oder Nein. Anschließend
        begründe Deine Einschätzung. Zuletzt weise darauf hin, dass Du nur eine KI bist und dies keine Rechtsberatung
        darstellt.'''

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt}
            ]
        )
        result = completion.choices[0].message.content

        return jsonify({'result': result})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing the request'}), 500


@app.route('/local_chat')
def local():
    # Llama 3.1: Chat Page
    return render_template('local_llm_chat.html')


@app.route("/local_analyze")
def analyze_pdf():
    # Llama 3.1: PDF Page
    return render_template('local_analyze_pdf.html')


@app.route("/ask", methods=["POST"])
def ask():
    # Llama 3.1: Execute Prompt
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is empty."}), 400

    response = ask_llama(question)
    return jsonify({"answer": response})


def ask_llama(question):
    # Llama 3.1: Execute Prompt
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.1:latest",
        "messages": [{"role": "user", "content": question}]
    }

    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code == 200:
                answer = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        answer += content
                return answer
            else:
                return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


@app.route("/upload", methods=["POST"])
def upload():
    # Llama 3.1: Extract content from PDF
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            with open(filepath, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = "".join(page.extract_text() for page in reader.pages)
            return jsonify({"text": text})
        except Exception as e:
            return jsonify({"error": f"Failed to read PDF: {e}"}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400


@app.route("/analyze", methods=["POST"])
def analyze():
    # Llama 3.1: Summarize PDF content
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided."}), 400

    summary = ask_llama(f"Provide a brief summary of the following text:\n{text}")
    return jsonify({"summary": summary})


@app.route('/input', methods=['GET', 'POST'])
def input_page():
    if request.method == 'POST':
        option_value = request.form.get('option')
        if option_value:
            with sqlite3.connect("database/database.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Options (value) VALUES (?)", (option_value,))
                conn.commit()
            return redirect(url_for('output_page'))
    return '''
        <form method="POST">
            <label for="option">Enter Value:</label>
            <input type="text" id="option" name="option">
            <button type="submit">Save</button>
        </form>
    '''


@app.route('/output', methods=['GET'])
def output_page():
    with sqlite3.connect("database/database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM Options")
        rows = cursor.fetchall()

    rows_html = "".join(f"<li>{row[0]}</li>" for row in rows)
    return f"""
        <ul>
            {rows_html}
        </ul>
        <a href="{url_for('input_page')}">Go Back</a>
    """


@app.route('/radiobuttons')
def radiobuttons():
    # Radiobuttons
    return render_template('radiobuttons.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    # Radiobuttons
    option1 = request.form.get('group1')
    option2 = request.form.get('group2')
    option3 = request.form.get('group3')
    option4 = request.form.get('group4')
    option5 = request.form.get('group5')
    option6 = request.form.get('group6')
    option7 = request.form.get('group7')
    option8 = request.form.get('group8')
    option9 = request.form.get('group9')

    # Determine the label text based on the selected option of the first radio group
    result = "yes" if option1 == 'option1_1' else "no"

    # Pass the selected values back to the template
    return render_template('radiobuttons.html', result=result, option1=option1, option2=option2,
                           option3=option3, option4=option4, option5=option5, option6=option6, option7=option7,
                           option8=option8, option9=option9)


@app.route('/about_us')
def about_us():
    # About us page
    return render_template('about_us.html')


@app.route('/impressum')
def impressum():
    # Impressum page
    return render_template('impressum.html')


@app.route('/disclaimer')
def disclaimer():
    # Disclaimer page
    return render_template('disclaimer.html')


def open_browser():
    # required to automatically start the browser once the webserver is running
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()

    app.run(debug=True)
