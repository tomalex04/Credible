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

    if (data && data.summary) {
      // Display summary exactly as it comes from the backend
      addMessage(data.summary, 'bot', true); // scrollable <pre> block
    } else {
      addMessage("Could not generate a summary.", 'bot');
    }
  } catch (e) {
    loader.remove();
    addMessage("Error checking news.", 'bot');
  }
}

function formatBackendData(data) {
  // If we have a summary, only display that
  if (data && data.summary) {
    if (typeof data.summary === 'string') {
      return data.summary;
    } else if (typeof data.summary === 'object' && data.summary.text) {
      return data.summary.text;
    } else {
      return JSON.stringify(data.summary, null, 2);
    }
  }
  
  // If no summary is available, return null so we can fall back to showing basic results
  return null;
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});
