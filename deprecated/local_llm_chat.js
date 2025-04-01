async function sendQuestion() {
    const inputField = document.getElementById('questionInput');
    const question = inputField.value.trim();

    if (question === "") {
        alert("Please enter a question.");
        return;
    }

    const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
    });

    const data = await response.json();
    inputField.value += "\\n" + data.answer;
}
