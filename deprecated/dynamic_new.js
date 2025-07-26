document.addEventListener('DOMContentLoaded', function() {
    loadInitialQuestion();
});

function loadInitialQuestion() {
    fetch('/get_fragen')
        .then(response => response.json())
        .then(fragen => {
            // Find the initial question (Initial: true/1)
            // Your /get_fragen route might need to return the Initial property!
            fetch('/get_frage/' + fragen[0].ID)
                .then(resp => resp.json())
                .then(q => {
                    if (q.Initial) {
                        renderQuestion(q);
                    } else {
                        // Fallback: find the initial one
                        for (const f of fragen) {
                            fetch('/get_frage/' + f.ID)
                                .then(resp2 => resp2.json())
                                .then(q2 => {
                                    if (q2.Initial) renderQuestion(q2);
                                });
                        }
                    }
                });
        });
}

function renderQuestion(questionData) {
    const container = document.getElementById('questionnaireContainer');
    // Basic select for Ja/Nein/Unsicher (customize with real options if you use tbl_antworten)
    container.innerHTML = `
        <div class="question-block">
            <label><b>${questionData.Text}</b></label>
            ${questionData.Bem ? `<div style="font-size:0.95em;color:#777">${questionData.Bem}</div>` : ""}
            <select id="answerSelect">
                <option value="">Bitte wählen...</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
                <option value="unsicher">Unsicher</option>
            </select>
        </div>
    `;

    document.getElementById('answerSelect').addEventListener('change', function(e) {
        const antwort = e.target.value;
        if (antwort) {
            callNextElement(questionData.ID, antwort);
        }
    });
}

function callNextElement(frage_id, antwort) {
    fetch('/next_element', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frage_id: frage_id, antwort: antwort })
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "Frage") {
            renderQuestion(data);
        } else if (data.type === "Prompt") {
            renderPrompt(data);
        } else if (data.done) {
            renderEndScreen(data.message);
        } else {
            document.getElementById('questionnaireContainer').innerHTML = '<div>Unbekanntes Element</div>';
        }
    });
}

// Render prompt (LLM) type
function renderPrompt(promptData) {
    const container = document.getElementById('questionnaireContainer');
    container.innerHTML = `
        <div class="prompt-block">
            <b>${promptData.Bez}</b>
            <div style="margin-bottom:0.5em">${promptData.System}</div>
            <input type="text" id="promptInput" placeholder="Ihre Beschreibung..." style="width:80%"/>
            <button id="promptSend">Absenden</button>
            <div id="promptResponse" style="margin-top:1em"></div>
        </div>
    `;
    document.getElementById('promptSend').onclick = function() {
        // Here you would call your LLM backend as you already do (e.g., /analyze_chatgpt)
        document.getElementById('promptResponse').innerText = 'Demo: Anfrage abgeschickt (hier käme die LLM-Antwort)';
    };
}

// End screen (Absage/Zusage or finish)
function renderEndScreen(message) {
    const container = document.getElementById('questionnaireContainer');
    container.innerHTML = `<div style="padding:2em;background:#efefef;border-radius:8px;text-align:center">${message || 'Fragebogen abgeschlossen.'}</div>`;
}
