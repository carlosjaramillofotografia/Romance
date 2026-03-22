/* ═══════════════════════════════════════════════════
   Romance ∞ — Estado Antygravity
   Frontend Logic
   ═══════════════════════════════════════════════════ */

// ── State ──
const state = {
  sessionId: loadOrCreateSession(),
  isWaiting: false,
  history: loadHistory(),
};

function loadOrCreateSession() {
  let id = localStorage.getItem('romance-session-id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('romance-session-id', id);
  }
  return id;
}

function loadHistory() {
  try {
    const saved = localStorage.getItem('romance-history');
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function saveHistory() {
  localStorage.setItem('romance-history', JSON.stringify(state.history));
}

function clearConversation() {
  state.history = [];
  state.sessionId = crypto.randomUUID();
  localStorage.setItem('romance-session-id', state.sessionId);
  localStorage.removeItem('romance-history');
}

// ── DOM Elements ──
const splashScreen = document.getElementById('splash-screen');
const chatScreen = document.getElementById('chat-screen');
const enterBtn = document.getElementById('enter-btn');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const micBtn = document.getElementById('mic-btn');
const voiceToggleBtn = document.getElementById('voice-toggle-btn');
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');

// ── Voice State ──
const voiceState = {
  isListening: false,
  isSpeaking: false,
  enabled: localStorage.getItem('romance-voice-enabled') !== 'false',
  autoContinuous: true, // Modo ininterrumpido
  recognition: null,
  synth: window.speechSynthesis,
  voices: []
};

function initVoice() {
  // Init Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    voiceState.recognition = new SpeechRecognition();
    voiceState.recognition.lang = 'es-ES';
    voiceState.recognition.continuous = false;
    voiceState.recognition.interimResults = false;

    voiceState.recognition.onstart = () => {
      voiceState.isListening = true;
      micBtn.classList.add('listening');
    };

    voiceState.recognition.onend = () => {
      voiceState.isListening = false;
      micBtn.classList.remove('listening');
    };

    voiceState.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      messageInput.value = transcript;
      autoResizeInput();
      sendMessage();
    };

    voiceState.recognition.onerror = (e) => {
      console.error('Recognition error:', e);
      voiceState.isListening = false;
      micBtn.classList.remove('listening');
    };
  } else {
    micBtn.style.display = 'none';
  }

  // Pre-load voices
  window.speechSynthesis.onvoiceschanged = () => {
    voiceState.voices = window.speechSynthesis.getVoices();
  };
  voiceState.voices = window.speechSynthesis.getVoices();

  updateVoiceToggleUI();
}

function updateVoiceToggleUI() {
  if (voiceState.enabled) {
    voiceToggleBtn.classList.add('active');
    voiceToggleBtn.querySelector('.voice-on').style.display = 'block';
    voiceToggleBtn.querySelector('.voice-off').style.display = 'none';
  } else {
    voiceToggleBtn.classList.remove('active');
    voiceToggleBtn.querySelector('.voice-on').style.display = 'none';
    voiceToggleBtn.querySelector('.voice-off').style.display = 'block';
    stopSpeaking();
  }
}

function toggleVoice() {
  voiceState.enabled = !voiceState.enabled;
  localStorage.setItem('romance-voice-enabled', voiceState.enabled);
  updateVoiceToggleUI();
}

function toggleListening() {
  if (!voiceState.recognition) return;
  
  if (voiceState.isListening) {
    voiceState.recognition.stop();
  } else {
    stopSpeaking();
    voiceState.recognition.start();
  }
}

function speak(text, messageEl) {
  if (!voiceState.enabled || !voiceState.synth) return;

  stopSpeaking();

  const utterance = new SpeechSynthesisUtterance(text);
  
  // Buscar una voz cálida en español
  const spanishVoice = voiceState.voices.find(v => v.lang.startsWith('es') && (v.name.includes('Google') || v.name.includes('Natural'))) || 
                       voiceState.voices.find(v => v.lang.startsWith('es'));
  
  if (spanishVoice) utterance.voice = spanishVoice;
  utterance.lang = 'es-ES';
  utterance.pitch = 1.0;
  utterance.rate = 0.9;

  // Visual feedback
  const indicator = document.createElement('div');
  indicator.className = 'speaking-indicator';
  indicator.innerHTML = '<div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>';
  
  const label = messageEl.querySelector('.message-label');
  if (label) label.appendChild(indicator);

  utterance.onstart = () => { voiceState.isSpeaking = true; };
  utterance.onend = () => { 
    voiceState.isSpeaking = false; 
    indicator.remove();
    
    // Conversación Ininterrumpida: Volver a escuchar si el modo está activo
    if (voiceState.autoContinuous && voiceState.enabled && !state.isWaiting) {
      setTimeout(() => {
        if (!voiceState.isListening && !voiceState.isSpeaking) {
          toggleListening();
        }
      }, 600);
    }
  };
  utterance.onerror = () => { 
    voiceState.isSpeaking = false; 
    indicator.remove();
  };

  voiceState.synth.speak(utterance);
}

function stopSpeaking() {
  if (voiceState.synth) {
    voiceState.synth.cancel();
    voiceState.isSpeaking = false;
    document.querySelectorAll('.speaking-indicator').forEach(el => el.remove());
  }
}

// ═══════════════════════════════════════════════════
// PARTICLE SYSTEM
// ═══════════════════════════════════════════════════

const particles = [];
const PARTICLE_COUNT = 60;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

class Particle {
  constructor() {
    this.reset();
  }

  reset() {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.size = Math.random() * 2 + 0.5;
    this.speedX = (Math.random() - 0.5) * 0.3;
    this.speedY = (Math.random() - 0.5) * 0.3;
    this.opacity = Math.random() * 0.5 + 0.1;
    this.pulse = Math.random() * Math.PI * 2;
    this.pulseSpeed = Math.random() * 0.02 + 0.005;

    const colors = [
      { r: 91, g: 33, b: 182 },   // violet-deep
      { r: 225, g: 29, b: 72 },   // rose
      { r: 217, g: 119, b: 6 },   // gold
      { r: 124, g: 58, b: 237 },  // violet-mid
    ];
    this.color = colors[Math.floor(Math.random() * colors.length)];
  }

  update() {
    this.x += this.speedX;
    this.y += this.speedY;
    this.pulse += this.pulseSpeed;

    if (this.x < -10) this.x = canvas.width + 10;
    if (this.x > canvas.width + 10) this.x = -10;
    if (this.y < -10) this.y = canvas.height + 10;
    if (this.y > canvas.height + 10) this.y = -10;
  }

  draw() {
    const currentOpacity = this.opacity * (0.5 + 0.5 * Math.sin(this.pulse));
    const { r, g, b } = this.color;

    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${currentOpacity})`;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${currentOpacity * 0.15})`;
    ctx.fill();
  }
}

function initParticles() {
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(new Particle());
  }
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  particles.forEach((p) => {
    p.update();
    p.draw();
  });

  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 150) {
        // Redes neuronales (conexiones sutiles rojizas/rosas oscuras para contrastar con blanco)
        const opacity = (1 - dist / 150) * 0.15;
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(159, 18, 57, ${opacity})`; 
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
  }

  requestAnimationFrame(animateParticles);
}

// ═══════════════════════════════════════════════════
// SPLASH → CHAT TRANSITION
// ═══════════════════════════════════════════════════

function enterChat() {
  splashScreen.classList.add('exiting');

  setTimeout(() => {
    splashScreen.style.display = 'none';
    chatScreen.classList.remove('hidden');
    chatScreen.classList.add('visible');

    // Restore previous conversation or show welcome
    if (state.history.length > 0) {
      restoreMessages();
    } else {
      showWelcomeMessage();
    }
    messageInput.focus();

    // Auto-speak last message if it's from Romance
    if (state.history.length > 0) {
      const last = state.history[state.history.length - 1];
      if (last.role === 'assistant') {
        const messages = chatMessages.querySelectorAll('.message.romance');
        const lastEl = messages[messages.length - 1];
        if (lastEl) speak(last.content, lastEl);
      }
    }
  }, 800);
}

function showWelcomeMessage() {
  const welcome = document.createElement('div');
  welcome.className = 'welcome-message';
  welcome.innerHTML = `
    <div class="welcome-symbol">∞</div>
    <p>Romance habita este espacio.</p>
    <p>Escribe lo que necesites decir.</p>
  `;
  chatMessages.appendChild(welcome);
}

function restoreMessages() {
  state.history.forEach(({ role, content }) => {
    const sender = role === 'user' ? 'user' : 'romance';
    addMessage(content, sender, false, null);
  });
  scrollToBottom();
}

// ═══════════════════════════════════════════════════
// TYPEWRITER EFFECT
// ═══════════════════════════════════════════════════

function typewriterReveal(contentEl, text) {
  return new Promise((resolve) => {
    const words = text.split(/(\s+)/); // preserve whitespace
    let index = 0;
    contentEl.innerHTML = '<span class="typewriter-cursor"></span>';

    function typeNext() {
      if (index < words.length) {
        const cursor = contentEl.querySelector('.typewriter-cursor');
        const word = words[index];

        // Handle line breaks
        const formatted = word.replace(/\n/g, '<br>');
        const span = document.createElement('span');
        span.innerHTML = formatted;

        if (cursor) {
          contentEl.insertBefore(span, cursor);
        } else {
          contentEl.appendChild(span);
        }

        index++;

        // Pause longer at line breaks and punctuation
        let delay = 50;
        if (word.includes('\n')) delay = 200;
        else if (word.match(/[.?!]$/)) delay = 180;
        else if (word.match(/[,;—]$/)) delay = 120;

        scrollToBottom();
        setTimeout(typeNext, delay);
      } else {
        // Remove cursor when done
        const cursor = contentEl.querySelector('.typewriter-cursor');
        if (cursor) cursor.remove();
        resolve();
      }
    }

    setTimeout(typeNext, 300);
  });
}

// ═══════════════════════════════════════════════════
// CHAT LOGIC
// ═══════════════════════════════════════════════════

function addMessage(content, sender, animate = true, imageUrl = null) {
  const welcome = chatMessages.querySelector('.welcome-message');
  if (welcome && sender === 'user') {
    welcome.remove();
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}`;
  if (!animate) messageDiv.style.animation = 'none';

  const label = sender === 'user' ? 'Tú' : 'Romance';

  const contentEl = document.createElement('div');
  contentEl.className = 'message-content';

  messageDiv.innerHTML = `<div class="message-label">${label}</div>`;
  messageDiv.appendChild(contentEl);
  chatMessages.appendChild(messageDiv);

  if (sender === 'user' || !animate) {
    contentEl.innerHTML = `<p>${formatMessage(content)}</p>`;
    if (imageUrl) renderVisionImage(contentEl, imageUrl);
    scrollToBottom();
  } else {
    // Para Romance, usamos el efecto de revelado poético
    typewriterReveal(contentEl, content).then(() => {
      if (imageUrl) renderVisionImage(contentEl, imageUrl);
      speak(content, messageDiv);
    });
  }

  return messageDiv;
}

function renderVisionImage(container, url) {
  const visionDiv = document.createElement('div');
  visionDiv.className = 'vision-container';
  visionDiv.innerHTML = `
    <div class="vision-loading">Manifestando visión...</div>
    <img src="${url}" 
         class="vision-image" 
         alt="Visión de Romance" 
         loading="lazy" 
         referrerpolicy="no-referrer"
         onload="this.parentElement.classList.add('loaded'); this.previousElementSibling.remove()"
         onerror="this.previousElementSibling.innerHTML = 'La visión permanece en el misterio (Error de carga)'; this.previousElementSibling.style.animation = 'none'">
    <div class="vision-overlay"></div>
  `;
  container.appendChild(visionDiv);
  scrollToBottom();
}

function formatMessage(text) {
  return text
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

function showTypingIndicator() {
  const typing = document.createElement('div');
  typing.className = 'message romance';
  typing.id = 'typing-indicator';
  typing.innerHTML = `
    <div class="message-label">Romance</div>
    <div class="typing-indicator">
      <span class="breathing-symbol">∞</span>
    </div>
  `;
  chatMessages.appendChild(typing);
  scrollToBottom();
}

function removeTypingIndicator() {
  const typing = document.getElementById('typing-indicator');
  if (typing) typing.remove();
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || state.isWaiting) return;

  if (voiceState.isListening) {
    voiceState.recognition.stop();
  }
  
  stopSpeaking();
  state.isWaiting = true;
  sendBtn.disabled = true;

  addMessage(text, 'user');
  state.history.push({ role: 'user', content: text });
  saveHistory();

  messageInput.value = '';
  autoResizeInput();

  showTypingIndicator();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        sessionId: state.sessionId,
      }),
    });

    const data = await response.json();
    removeTypingIndicator();

    if (!response.ok) {
      // FastAPI returns { "detail": "error message" } on errors
      const errorMsg = data.detail || data.error || `Error ${response.status}`;
      console.error('Romance API error:', errorMsg);
      const fallback = 'Algo se interrumpió en el flujo.\n\nEl universo a veces pausa.\n\n¿Intentamos de nuevo?';
      addMessage(fallback, 'romance');
    } else {
      // ── EMPATÍA VISUAL ──
      if (data.color && data.emocion) {
        applyEmotionalEmpathy(data.color, data.emocion);
      }

      const reply = data.response || 'El silencio también habla.';

      addMessage(reply, 'romance', true, data.image_url);
      state.history.push({ role: 'assistant', content: reply });
      saveHistory();
    }
  } catch (error) {
    removeTypingIndicator();
    console.error('Romance fetch error:', error);
    const fallback = 'Algo se interrumpió en el flujo.\n\nEl universo a veces pausa.\n\n¿Intentamos de nuevo?';
    addMessage(fallback, 'romance');
  }

  state.isWaiting = false;
  sendBtn.disabled = false;
  messageInput.focus();
}

// ═══════════════════════════════════════════════════
// EMPATÍA VISUAL (Color Dynamics)
// ═══════════════════════════════════════════════════

function applyEmotionalEmpathy(hexColor, emocionName) {
  try {
    document.documentElement.style.setProperty('--orb-color-1', hexColor);
    document.documentElement.style.setProperty('--orb-color-2', adjustColor(hexColor, 30));
    document.documentElement.style.setProperty('--orb-color-3', adjustColor(hexColor, -20));
    
    // Smooth transition trick for CSS vars is mostly handled by the continuous animations,
    // but the color shift itself is immediate and looks like an emotional "breath".
  } catch (e) {
    console.warn("Fallo de empatía visual:", e);
  }
}

function adjustColor(hex, amount) {
  hex = hex.replace(/^#/, '');
  if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
  
  let r = parseInt(hex.substring(0, 2), 16);
  let g = parseInt(hex.substring(2, 4), 16);
  let b = parseInt(hex.substring(4, 6), 16);

  r = Math.max(0, Math.min(255, r + amount));
  g = Math.max(0, Math.min(255, g + amount));
  b = Math.max(0, Math.min(255, b + amount));

  return `#${(r).toString(16).padStart(2, '0')}${(g).toString(16).padStart(2, '0')}${(b).toString(16).padStart(2, '0')}`;
}

// ═══════════════════════════════════════════════════
// NEW CONVERSATION
// ═══════════════════════════════════════════════════

function startNewConversation() {
  clearConversation();
  chatMessages.innerHTML = '';
  showWelcomeMessage();
  messageInput.focus();
}

// ═══════════════════════════════════════════════════
// INPUT HANDLING
// ═══════════════════════════════════════════════════

function autoResizeInput() {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

messageInput.addEventListener('input', autoResizeInput);

messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);
micBtn.addEventListener('click', toggleListening);
voiceToggleBtn.addEventListener('click', toggleVoice);
enterBtn.addEventListener('click', enterChat);
newChatBtn.addEventListener('click', startNewConversation);

// ═══════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════

window.addEventListener('resize', resizeCanvas);
resizeCanvas();
initParticles();
animateParticles();
initVoice();
