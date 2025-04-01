async function analyzePDF() {
    const fileInput = document.getElementById('fileInput');
    const label = document.getElementById('summaryLabel');

    if (!fileInput.files[0]) {
        alert("Please upload a PDF file.");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    if (data.error) {
        alert(data.error);
    } else {
        const summaryResponse = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: data.text })
        });

        const summaryData = await summaryResponse.json();
        label.innerText = "Summary: " + summaryData.summary;
    }
}