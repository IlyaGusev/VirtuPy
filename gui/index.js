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


function addMessageToChat(message) {
    const messagesContainer = document.getElementById("messages");
    const messageElement = document.createElement("div");
    messageElement.textContent = message;
    messagesContainer.appendChild(messageElement);
};


function bindSocket(socket, model) {
    socket.onmessage = (event) => {
        if (event.data instanceof Blob) {
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
            addMessageToChat(`Она: ${data.message}`);
        }
        if (data.expression) {
            model.expression(HARU_EXPERSSIONS[data.expression]);
        }
    };
};

document.getElementById("send-message").addEventListener("click", function() {
    const messageInput = document.getElementById("message-input");
    const message = messageInput.value;
    SOCKET.send(message);
    addMessageToChat(`Вы: ${message}`);
    messageInput.value = "";
});


document.getElementById("message-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        document.getElementById("send-message").click();
    }
});


(async function main() {
    const app = new PIXI.Application({
        view: document.getElementById("canvas"),
        autoStart: true,
        resizeTo: window
    });

    app.stage.addChild(MODEL);

    MODEL.scale.set(0.25);
    MODEL.x = 200;

    bindSocket(SOCKET, MODEL);

    const expressionNames = MODEL.internalModel.motionManager.expressionManager.definitions.map(def => def.Name);
    const expressionSelect = document.getElementById("expression-select");
    const defaultOption = document.createElement("option");
    expressionSelect.innerHTML = '';
    defaultOption.textContent = 'Select an expression';
    defaultOption.value = '';
    expressionSelect.appendChild(defaultOption);

    expressionNames.forEach(expression => {
        const option = document.createElement('option');
        option.value = expression;
        option.textContent = expression;
        expressionSelect.appendChild(option);
    });
    expressionSelect.addEventListener("change", function() {
        MODEL.expression(this.value);
    });
})();

