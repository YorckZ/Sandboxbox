function updateDropdown11() {
	let dropdown11 = document.getElementById("dropdown11").value;
	let dynamicArea11 = document.getElementById("dynamicArea11");
	let ZusageArea = document.getElementById("ZusageArea");
	let AbsageArea = document.getElementById("AbsageArea");
	dynamicArea11.innerHTML = "";
	ZusageArea.innerHTML = "";
	AbsageArea.innerHTML = "";

    // Does Nothing
    if (dropdown11 === "n.a.") {
        clear()
    }

    // Calls F1.2 in dynamicArea12
    else if (dropdown11 === "ja") {
        clear()
		dynamicArea11.innerHTML = `
			<label for="dropdown12">
			    1.2) Findet die Verarbeitung der personenbezogenen Daten im Rahmen einer Tätigkeit einer Niederlassung Ihres Unternehmens in der EU statt?
            </label>
			<select id="dropdown12" onchange="updateDropdown12()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
                <option value="unsicher">Ich bin mir unsicher.</option>
			</select>
			<div id="dynamicArea12" style="margin-top:20px;"></div>
		`;
    }

    // Cancels the questionnaire
    else if (dropdown11 === "nein") {
        clear()
        Absage()
    }

    // Handle the "unsicher" case
    if (dropdown11 === "unsicher") {
        clear();
        dynamicArea11.innerHTML = `
            <label for="promptInput">Fragen Sie SANDy, die Sandbox-KI. Bitte beschreiben Sie die Art der Daten, die in Ihrem Unternehmen verarbeitet werden.</label>
            <input type="text" id="promptInput" placeholder="Ihre Beschreibung für SANDy..." />
            <br>
            <br>
            <label for="fileInput">(Optional): Stellen Sie SANDy Dokumente zur Auswertung zur Verfügung:</label>
            <input type="file" id="fileInput" accept="application/pdf" />
            <br>
            <br>
            <button id="analyzeButton">Einschätzung von SANDy einholen</button>
            <br>
            <!-- <label id="outputLabel"></label> -->
            <div id="outputLabel" class="output-box" style="display: none;"></div>
        `;

        // Add an event listener to the "Analyze" button
        document.getElementById("analyzeButton").addEventListener("click", async () => {
            event.preventDefault();
            let promptInput = document.getElementById("promptInput").value;
            let fileInput = document.getElementById("fileInput").files[0]; // Get the selected file
            let outputLabel = document.getElementById("outputLabel");

            if (!promptInput) {
                outputLabel.style.display = "block"; // Make it visible
                outputLabel.textContent = "Please enter a prompt.";
                return;
            }

            outputLabel.style.display = "block"; // Show the outputLabel
            // outputLabel.textContent = "Analyzing...";

            let formData = new FormData();
            formData.append('prompt', promptInput);
            if (fileInput) {
                formData.append('file', fileInput);
            }

            try {
                // Call the Flask /analyze route
                const response = await fetch('/analyze_chatgpt', {
                    method: 'POST',
                    //headers: {
                    //    'Content-Type': 'application/json'
                    //},
                    //body: JSON.stringify({ prompt: promptInput }) // Send the prompt to Flask
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.error) {
                    outputLabel.textContent = `Error: ${data.error}`;
                    } else {
                        outputLabel.textContent = data.result; // Display the result
                    }
                    outputLabel.style.display = "block"; // Make the label visible
                } catch (error) {
                    console.error(error);
                    outputLabel.textContent = "An error occurred while analyzing. 2";
                    outputLabel.style.display = "block"; // Make the label visible
                }
            });
    }

    // Zu- und Absage anzeigen
    else if (dropdown11 === "ZuAbsage") {
        clear()
        Zusage()
        Absage()
    }
}

function updateDropdown12() {
	let dropdown12 = document.getElementById("dropdown12").value;
	let dynamicArea12 = document.getElementById("dynamicArea12");
	dynamicArea12.innerHTML = "";

    // Does Nothing
    if (dropdown12 === "n.a.") {
        clear()
    }

    // Calls F1.3 in dynamicArea13
    else if (dropdown12 === "ja") {
        clear()
		dynamicArea12.innerHTML = `
			<label for="dropdown13">
			    1.3) Fällt Ihr Unternehmen in den Zuständigkeitsbereich der Landesdatenschutzbehörde Rheinland-Pfalz?
            </label>
			<select id="dropdown13" onchange="updateDropdown13()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea13" style="margin-top:20px;"></div>
		`;
	}

	// Cancels the questionnaire
	else if (dropdown12 === "nein") {
	    clear()
        dynamicArea12.innerHTML = `
			<label for="dropdown121">
			    1.2.1) Befindet sich die Niederlassung Ihres Auftragsverarbeiters in der Europäischen Union?
            </label>
			<select id="dropdown121" onchange="updateDropdown121()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea121" style="margin-top:20px;"></div>
		`;
	}

	// Calls an LLM for help
	else if (dropdown12 === "unsicher") {
	    clear()
	}
}

function updateDropdown121() {
	let dropdown121 = document.getElementById("dropdown121").value;
	let dynamicArea121 = document.getElementById("dynamicArea121");
	dynamicArea121.innerHTML = "";

    // Does Nothing
    if (dropdown121 === "n.a.") {
        clear()
    }

    // Calls F1.3 in dynamicArea13
    else if (dropdown121 === "ja") {
        clear()
		dynamicArea121.innerHTML = `
			<label for="dropdown13">
			    1.3) Fällt Ihr Unternehmen in den Zuständigkeitsbereich der Landesdatenschutzbehörde Rheinland-Pfalz?
            </label>
			<select id="dropdown13" onchange="updateDropdown13()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea13" style="margin-top:20px;"></div>
		`;
    }

	// Cancels the questionnaire
	else if (dropdown121 === "nein") {
	    clear()
        dynamicArea121.innerHTML = `
			<label for="dropdown122">
			    1.2.2) Verarbeitet Ihr Unternehmen personenbezogene Daten, um Waren oder Dienstleistungen an Personen in der Europäischen Union anzubieten?
            </label>
			<select id="dropdown122" onchange="updateDropdown122()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea122" style="margin-top:20px;"></div>
		`;
	}
}

function updateDropdown122() {
	let dropdown122 = document.getElementById("dropdown122").value;
	let dynamicArea122 = document.getElementById("dynamicArea122");
	dynamicArea122.innerHTML = "";

    // Does Nothing
    if (dropdown122 === "n.a.") {
        clear()
    }

    else if (dropdown122 === "ja") {
        clear()
        dynamicArea122.innerHTML = `
			<label for="dropdown13">
			    1.3) Fällt Ihr Unternehmen in den Zuständigkeitsbereich der Landesdatenschutzbehörde Rheinland-Pfalz?
            </label>
			<select id="dropdown13" onchange="updateDropdown13()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea13" style="margin-top:20px;"></div>
		`;
    }

    else if (dropdown122 === "nein") {
        clear()
        dynamicArea122.innerHTML = `
			<label for="dropdown13">
			    1.2.3) Analysiert Ihr Unternehmen das Internetverhalten von Personen in der Europäischen Union?
            </label>
			<select id="dropdown123" onchange="updateDropdown123()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea123" style="margin-top:20px;"></div>
		`;
    }
}

function updateDropdown123() {
	let dropdown123 = document.getElementById("dropdown123").value;
	let dynamicArea123 = document.getElementById("dynamicArea123");
	dynamicArea123.innerHTML = "";

    // Does Nothing
    if (dropdown123 === "n.a.") {
        clear()
    }

    // Calls F1.3 in dynamicArea13
    if (dropdown123 === "ja") {
        clear()
        dynamicArea123.innerHTML = `
			<label for="dropdown13">
			    1.3) Fällt Ihr Unternehmen in den Zuständigkeitsbereich der Landesdatenschutzbehörde Rheinland-Pfalz?
            </label>
			<select id="dropdown13" onchange="updateDropdown13()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
			</select>
			<div id="dynamicArea13" style="margin-top:20px;"></div>
		`;
    }

    // Cancels the questionnaire
    if (dropdown123 === "nein") {
        clear()
        Absage()
    }

}

function updateDropdown13() {
	let dropdown13 = document.getElementById("dropdown13").value;
	let dynamicArea13 = document.getElementById("dynamicArea13");
	dynamicArea13.innerHTML = "";

    // Does Nothing
    if (dropdown13 === "n.a.") {
        clear()
    }

    // Calls F2.1 in dynamicArea21
    else if (dropdown13 === "ja") {
        clear()
		dynamicArea13.innerHTML = `
		    <h1>2. Auswahlfragen</h1>
			<label for="dropdown21">2.1) Welcher Branche Ordnen Sie die Anwendung zu?</label>
			<select id="dropdown21" onchange="updateDropdown21()">
                <option value="n.a.">n.a.</option>
			</select>
			<div id="dynamicArea21" style="margin-top:20px;"></div>
		`;
	}

	// Cancels the questionnaire
	else if (dropdown13 === "nein") {
	    clear()
        Absage()
	}
}

function Zusage() {
	let ZusageArea = document.getElementById("ZusageArea");
	ZusageArea.innerHTML = "";

    ZusageArea.innerHTML = `
        <div style="background-color: #d4edda; border: 1px solid black; border-radius: 8px; padding: 15px;">
            <h1>Positive Einschätzung:</h1>
            Unter Berücksichtigung der von Ihnen gemachten Angaben scheint es, dass die Vorgaben der DSGVO auf Ihr Unternehmen anzuwenden sind.<br>
            Um innovative Produkte und Dienstleistungen datenschutzkonform anbieten zu können, empfiehlt sich ein Austausch mit den Datenschutzexperten des LfDI.<br>
            <br>
            Nehmen Sie gerne Kontakt zu uns auf unter <a href="tel:+49-0123-456789012">0123-456789012</a> oder unter <a href="mailto:eine@email.de">eine@email.de</a>.
        </div>
    `;
}

function Absage() {
	let AbsageArea = document.getElementById("AbsageArea");
	AbsageArea.innerHTML = "";

    AbsageArea.innerHTML = `
        <div style="background-color: #f8d7da; border: 1px solid black; border-radius: 8px; padding: 15px;">
            <h1>Negative Einschätzung:</h1>
            Unter Berücksichtigung der von Ihnen gemachten Angaben scheint es, dass die Vorgaben der DSGVO nicht auf Ihr Unternehmen anzuwenden sind.<br>
            Um innovative Produkte und Dienstleistungen datenschutzkonform anbieten zu können, empfiehlt sich ein Austausch mit den Datenschutzexperten des LfDI.<br>
            <br>
            Nehmen Sie dennoch gerne Kontakt zu uns auf unter <a href="tel:+49-0123-456789012">0123-456789012</a> oder unter <a href="mailto:eine@email.de">eine@email.de</a>, um eine fachkundige Meinung einzuholen.
        </div>
    `;
}

function clear() {
	let ZusageArea = document.getElementById("ZusageArea");
	let AbsageArea = document.getElementById("AbsageArea");
	ZusageArea.innerHTML = "";
	AbsageArea.innerHTML = "";
}