window.PIXI = PIXI;

const MODEL_PATH = "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_greeter_t03.model3.json";
const DEFAULT_WS_ADDR = "ws://159.69.16.3:5000/ws";
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
            model.expression(data.expression);
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
})();

