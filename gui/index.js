window.PIXI = PIXI;

const MODEL_PATH = "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_greeter_t03.model3.json";
const HARU_EXPERSSIONS = {
    smiling: "f00",
    sad: "f03",
    happy: "f04",
    scared: "f05",
    shy: "f06",
    tired: "f07",
    angry: "f02",
};
const DEFAULT_WS_ADDR = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/virtupy/ws`;
const MODEL = await PIXI.live2d.Live2DModel.from(MODEL_PATH);
const SOCKET = new WebSocket(DEFAULT_WS_ADDR);

const messagesContainer = document.getElementById("messages");
const typingIndicator = document.getElementById("typing-indicator");
const chatContainer = document.getElementById("chat-container");
const chatHeader = document.getElementById("chat-header");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-message");
const expressionToggle = document.getElementById("expression-toggle");
const expressionPanel = document.getElementById("expression-panel");
const expressionList = document.getElementById("expression-list");


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


function bindSocket(socket, model) {
    socket.onmessage = (event) => {
        if (event.data instanceof Blob) {
            hideTypingIndicator();
            const audioURL = URL.createObjectURL(event.data);
            model.speak(audioURL);
            return;
        }
        let data;
        try {
            data = JSON.parse(event.data);
            console.log(data);
        } catch (error) {
            console.log(error);
            return;
        }
        if (!data) {
            return;
        }
        if (data.message) {
            hideTypingIndicator();
            addMessageToChat(data.message, false);
        }
        if (data.expression) {
            model.expression(HARU_EXPERSSIONS[data.expression]);
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


expressionToggle.addEventListener("click", function(e) {
    e.stopPropagation();
    expressionPanel.classList.toggle("open");
});


document.addEventListener("click", function(e) {
    if (!expressionPanel.contains(e.target) && !expressionToggle.contains(e.target)) {
        expressionPanel.classList.remove("open");
    }
});


function positionModel(model, app) {
    const width = app.renderer.width;
    const height = app.renderer.height;
    const mobile = isMobile();

    if (mobile) {
        const scale = Math.min(width / 1800, height / 2400);
        model.scale.set(scale);
        model.x = width / 2 - (model.width / 2);
        model.y = -height * 0.1;
    } else {
        const scale = Math.min(width / 2000, height / 2000);
        model.scale.set(scale);
        model.x = width * 0.05;
        model.y = 0;
    }
}


(async function main() {
    const app = new PIXI.Application({
        view: document.getElementById("canvas"),
        autoStart: true,
        resizeTo: window,
        backgroundAlpha: 0
    });

    app.stage.addChild(MODEL);
    positionModel(MODEL, app);

    window.addEventListener('resize', () => {
        positionModel(MODEL, app);
    });

    bindSocket(SOCKET, MODEL);

    const expressionNames = MODEL.internalModel.motionManager.expressionManager.definitions.map(def => def.Name);
    let currentExpression = '';

    expressionNames.forEach(expression => {
        const button = document.createElement('button');
        button.className = 'expression-btn';
        button.textContent = expression;
        button.addEventListener('click', () => {
            MODEL.expression(expression);
            document.querySelectorAll('.expression-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentExpression = expression;
            if (isMobile()) {
                expressionPanel.classList.remove('open');
            }
        });
        expressionList.appendChild(button);
    });
})();
