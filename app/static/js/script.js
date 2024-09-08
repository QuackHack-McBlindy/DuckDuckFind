// Get elements
const haLink = document.getElementById('ha-link');
const popup = document.getElementById('popup');
const popupOverlay = document.getElementById('popup-overlay');
const closeButton = document.getElementById('close-button');
const copyButton = document.getElementById('copy-button');

// Show popup when link is clicked
haLink.addEventListener('click', function(event) {
    event.preventDefault();
    popup.style.display = 'block';
    popupOverlay.style.display = 'block';
});

// Close popup
closeButton.addEventListener('click', function() {
    popup.style.display = 'none';
    popupOverlay.style.display = 'none';
});

// Close popup when Esc key is pressed
document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") { // Modern browsers use 'Escape'
        closePopup();
    }
});


// Copy text to clipboard
copyButton.addEventListener('click', function() {
    const code = `
shell_command:
  duckduckfind: >
    curl -X POST http://localhost:5556/ -H "Content-Type: application/json" -d '{"query": "{{ query }}"}'

intent_script:
  duckduckfind:
    action:   
      - service: shell_command.duckduckfind
        data: 
          query: "{{ query }}"
        response_variable: action_response
      - stop: ""
        response_variable: action_response   
    speech:
      text: "{{ action_response['stdout'] }}"
    `.trim(); // This removes unnecessary indentation

    // Attempt to use the Clipboard API
    if (navigator.clipboard) {
        navigator.clipboard.writeText(code).then(function() {
            alert("Code copied to clipboard!");
       }).catch(function(err) {
            console.error('Could not copy text: ', err);
            fallbackCopyText(code); // Fallback method in case of failure
        });
    } else {
        fallbackCopyText(code); // Fallback for older browsers
    }
});

// Fallback function to copy text using a temporary text area
function fallbackCopyText(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        alert('Code copied to clipboard (fallback method)!');
    } catch (err) {
        console.error('Fallback: Could not copy text', err);
    }
    document.body.removeChild(textArea);
}

// Function to close the popup and overlay
function closePopup() {
    popup.style.display = 'none';
    popupOverlay.style.display = 'none';
}
