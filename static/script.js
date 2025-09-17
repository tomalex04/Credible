const chat = document.getElementById('chat');
const input = document.getElementById('query');
const sendBtn = document.getElementById('sendBtn');

function addMessage(text, sender, isPre = false) {
  const msg = document.createElement('div');
  msg.classList.add('message', sender);
  
  // Add special class for pre-formatted messages to style them properly
  if (isPre) {
    msg.classList.add('pre-formatted');
    
    // For pre-formatted text (terminal output)
    const pre = document.createElement('pre');
    pre.textContent = text;
    
    // No inline styles - all styling comes from CSS
    msg.appendChild(pre);
  } else {
    msg.textContent = text;
  }

  chat.appendChild(msg);
  
  // Smooth scroll to new message
  setTimeout(() => {
    msg.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, 100);
  
  return msg;
}

function extractValuesFromJson(jsonObj) {
  if (!jsonObj) return "No data received";
  
  // Just output the summary value without any processing
  if (jsonObj.summary) {
    return jsonObj.summary;
  }
  
  // If no summary field exists, output everything as-is
  return JSON.stringify(jsonObj);
}

async function sendMessage() {
  const query = input.value.trim();
  if (!query) return;

  const bg = document.getElementById('chat-background');
  if (bg && !bg.classList.contains('blurred')) {
    bg.classList.add('blurred');
  }

  addMessage(query, 'user');
  input.value = '';

  const loader = addMessage('Processing...', 'bot');

  try {
    const response = await fetch('/api/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    });

    const data = await response.json();
    loader.remove();

    // Simply extract and display raw values from the JSON response
    const rawOutput = extractValuesFromJson(data);
    addMessage(rawOutput, 'bot', true);
  } catch (e) {
    loader.remove();
    addMessage("Error checking news: " + e.message, 'bot');
  }
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});
