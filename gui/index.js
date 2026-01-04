window.PIXI = PIXI;

const DEFAULT_WS_ADDR = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/virtupy/ws`;
const API_BASE = '/virtupy/api';

let currentModel = null;
let currentModelKey = 'haru';
let currentExpressionMap = {};
let availableModels = {};
let app = null;

const messagesContainer = document.getElementById("messages");
const typingIndicator = document.getElementById("typing-indicator");
const chatContainer = document.getElementById("chat-container");
const chatHeader = document.getElementById("chat-header");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-message");
const settingsToggle = document.getElementById("settings-toggle");
const settingsPanel = document.getElementById("settings-panel");
const expressionList = document.getElementById("expression-list");
const modelSelect = document.getElementById("model-select");
const languageSelect = document.getElementById("language-select");
const speakerSelect = document.getElementById("speaker-select");
const llmSelect = document.getElementById("llm-select");

const SOCKET = new WebSocket(DEFAULT_WS_ADDR);


function addMessageToChat(message, isUser = false) {
    const messageElement = document.createElement("div");
    messageElement.className = `message ${isUser ? 'user' : 'bot'}`;
    messageElement.textContent = message;
    messagesContainer.insertBefore(messageElement, typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function showTypingIndicator() {
    typingIndicator.classList.add('active');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
}


let currentBotMessage = null;
let audioQueue = [];
let isPlayingAudio = false;
let currentAudio = null;

function playNextAudio() {
    if (audioQueue.length === 0) {
        isPlayingAudio = false;
        return;
    }
    isPlayingAudio = true;
    const audioURL = audioQueue.shift();

    currentAudio = new Audio(audioURL);
    currentAudio.onended = () => {
        URL.revokeObjectURL(audioURL);
        playNextAudio();
    };
    currentAudio.onerror = () => {
        URL.revokeObjectURL(audioURL);
        playNextAudio();
    };

    if (currentModel && currentModel.internalModel && currentModel.internalModel.motionManager) {
        currentModel.speak(audioURL);
        currentAudio.muted = true;
    }

    currentAudio.play().catch(() => playNextAudio());
}

function queueAudio(blob) {
    const audioURL = URL.createObjectURL(blob);
    audioQueue.push(audioURL);
    if (!isPlayingAudio) {
        playNextAudio();
    }
}

function bindSocket(socket) {
    socket.onopen = () => {
        socket.send(JSON.stringify({ model: currentModelKey }));
    };

    socket.onmessage = (event) => {
        if (event.data instanceof Blob) {
            queueAudio(event.data);
            return;
        }
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            console.log(error);
            return;
        }
        if (!data) {
            return;
        }

        // Handle expression
        if (data.expression && currentModel) {
            const exprId = currentExpressionMap[data.expression];
            if (exprId) {
                currentModel.expression(exprId);
            }
            updateActiveExpression(exprId || data.expression);
        }

        // Handle streamed text
        if (data.text) {
            hideTypingIndicator();
            if (!currentBotMessage) {
                currentBotMessage = document.createElement("div");
                currentBotMessage.className = 'message bot';
                messagesContainer.insertBefore(currentBotMessage, typingIndicator);
            }
            currentBotMessage.textContent += data.text;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Handle completion
        if (data.done) {
            currentBotMessage = null;
        }
    };
}


function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    SOCKET.send(message);
    addMessageToChat(message, true);
    messageInput.value = "";
    messageInput.style.height = 'auto';
    showTypingIndicator();
}


sendButton.addEventListener("click", sendMessage);


messageInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});


messageInput.addEventListener("input", function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});


function isMobile() {
    return window.innerWidth < 768;
}


chatHeader.addEventListener("click", function() {
    if (isMobile()) {
        chatContainer.classList.toggle("collapsed");
    }
});


settingsToggle.addEventListener("click", function(e) {
    e.stopPropagation();
    settingsPanel.classList.toggle("open");
});


document.addEventListener("click", function(e) {
    if (!settingsPanel.contains(e.target) && !settingsToggle.contains(e.target)) {
        settingsPanel.classList.remove("open");
    }
});


function positionModel(model) {
    if (!model || !app) return;
    const width = app.renderer.width;
    const height = app.renderer.height;
    const mobile = isMobile();

    model.anchor.set(0.5, 0.5);

    const modelHeight = model.internalModel.originalHeight || model.height;
    const modelWidth = model.internalModel.originalWidth || model.width;

    const targetHeight = height * (mobile ? 0.5 : 0.85);
    const targetWidth = width * (mobile ? 0.8 : 0.5);

    const scaleByHeight = targetHeight / modelHeight;
    const scaleByWidth = targetWidth / modelWidth;
    const scale = Math.min(scaleByHeight, scaleByWidth);

    model.scale.set(scale);

    if (mobile) {
        model.x = width / 2;
        model.y = height * 0.35;
    } else {
        model.x = width * 0.3;
        model.y = height * 0.55;
    }
}


async function loadModel(modelKey) {
    const modelData = availableModels[modelKey];
    if (!modelData) return;

    modelSelect.disabled = true;
    currentModelKey = modelKey;

    if (SOCKET.readyState === WebSocket.OPEN) {
        SOCKET.send(JSON.stringify({ model: modelKey }));
    }

    if (currentModel) {
        app.stage.removeChild(currentModel);
        currentModel.destroy();
        currentModel = null;
    }

    try {
        const model = await PIXI.live2d.Live2DModel.from(modelData.url);
        currentModel = model;
        currentExpressionMap = modelData.expressions || {};

        app.stage.addChild(model);
        positionModel(model);

        updateExpressionList();
    } catch (error) {
        console.error("Failed to load model:", error);
    }

    modelSelect.disabled = false;
}


function updateActiveExpression(expressionId) {
    document.querySelectorAll('.expression-btn').forEach(btn => {
        const btnExpr = btn.dataset.expression;
        const btnExprId = btn.dataset.expressionId;
        if (btnExpr === expressionId || btnExprId === expressionId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}


function updateExpressionList() {
    expressionList.innerHTML = '';

    if (!currentModel) return;

    // Use mapped expression names (human-readable) if available
    const mappedNames = Object.keys(currentExpressionMap);

    if (mappedNames.length > 0) {
        mappedNames.forEach(name => {
            const button = document.createElement('button');
            button.className = 'expression-btn';
            button.textContent = name.charAt(0).toUpperCase() + name.slice(1);
            button.dataset.expression = name;
            button.dataset.expressionId = currentExpressionMap[name];
            button.addEventListener('click', () => {
                currentModel.expression(currentExpressionMap[name]);
                updateActiveExpression(name);
            });
            expressionList.appendChild(button);
        });
        return;
    }

    // Fall back to model's built-in expressions
    let expressionNames = [];
    try {
        const mgr = currentModel.internalModel?.motionManager?.expressionManager;
        if (mgr && mgr.definitions) {
            expressionNames = mgr.definitions.map(def => def.Name || def.name || def.File?.replace(/\.exp3?\.json$/i, ''));
        }
    } catch (e) {
        console.log("Could not get expressions from model");
    }

    if (expressionNames.length === 0) {
        const noExpr = document.createElement('span');
        noExpr.style.color = 'var(--text-secondary)';
        noExpr.style.fontSize = '12px';
        noExpr.textContent = 'No expressions available';
        expressionList.appendChild(noExpr);
        return;
    }

    expressionNames.forEach(expression => {
        if (!expression) return;
        const button = document.createElement('button');
        button.className = 'expression-btn';
        button.textContent = expression;
        button.dataset.expression = expression;
        button.dataset.expressionId = expression;
        button.addEventListener('click', () => {
            currentModel.expression(expression);
            updateActiveExpression(expression);
        });
        expressionList.appendChild(button);
    });
}


async function fetchModels() {
    try {
        const response = await fetch(`${API_BASE}/models`);
        availableModels = await response.json();

        modelSelect.innerHTML = '';
        for (const [key, data] of Object.entries(availableModels)) {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = data.name;
            modelSelect.appendChild(option);
        }

        modelSelect.value = 'haru';
        await loadModel('haru');
    } catch (error) {
        console.error("Failed to fetch models:", error);
    }
}


let availableVoices = {};

async function fetchVoices() {
    try {
        const response = await fetch(`${API_BASE}/voices`);
        const data = await response.json();
        availableVoices = data.available;

        languageSelect.innerHTML = '';
        const langNames = { ru: 'Russian', en: 'English', de: 'German', es: 'Spanish', fr: 'French' };

        for (const lang of Object.keys(availableVoices)) {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = langNames[lang] || lang;
            languageSelect.appendChild(option);
        }

        languageSelect.value = data.default.language;
        updateSpeakerOptions(availableVoices[data.default.language], data.default.speaker);
    } catch (error) {
        console.error("Failed to fetch voices:", error);
    }
}


function updateSpeakerOptions(speakers, currentSpeaker = null) {
    speakerSelect.innerHTML = '';

    for (const speaker of speakers) {
        const option = document.createElement('option');
        option.value = speaker;
        option.textContent = speaker;
        speakerSelect.appendChild(option);
    }

    if (currentSpeaker) {
        speakerSelect.value = currentSpeaker;
    }
}


function sendVoice(language, speaker) {
    if (SOCKET.readyState === WebSocket.OPEN) {
        SOCKET.send(JSON.stringify({ voice: { language, speaker } }));
    }
}


languageSelect.addEventListener('change', function() {
    const lang = this.value;
    const speakers = availableVoices[lang] || [];
    updateSpeakerOptions(speakers);

    if (speakers.length > 0) {
        sendVoice(lang, speakers[0]);
    }
});


speakerSelect.addEventListener('change', function() {
    sendVoice(languageSelect.value, this.value);
});


modelSelect.addEventListener('change', function() {
    loadModel(this.value);
});


async function fetchLLMs() {
    try {
        const response = await fetch(`${API_BASE}/llm`);
        const data = await response.json();

        llmSelect.innerHTML = '';
        for (const model of data.available) {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            llmSelect.appendChild(option);
        }

        llmSelect.value = data.default;
    } catch (error) {
        console.error("Failed to fetch LLMs:", error);
    }
}


llmSelect.addEventListener('change', function() {
    if (SOCKET.readyState === WebSocket.OPEN) {
        SOCKET.send(JSON.stringify({ llm: this.value }));
    }
});


(async function main() {
    app = new PIXI.Application({
        view: document.getElementById("canvas"),
        autoStart: true,
        resizeTo: window,
        backgroundAlpha: 0
    });

    window.addEventListener('resize', () => {
        positionModel(currentModel);
    });

    bindSocket(SOCKET);

    await Promise.all([fetchModels(), fetchVoices(), fetchLLMs()]);
})();
