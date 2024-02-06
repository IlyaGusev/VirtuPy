window.PIXI = PIXI;

const cubism4Model = "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_greeter_t03.model3.json";
const DEFAULT_WS_ADDR = "ws://159.69.16.3:5000/ws";
const model4 = await PIXI.live2d.Live2DModel.from(cubism4Model);
const socket = new WebSocket(DEFAULT_WS_ADDR);

function bindSocket(socket, model) {
    socket.onmessage = (event) => {
        if (event.data instanceof Blob) {
            const audioURL = URL.createObjectURL(event.data);
            const audio = new Audio(audioURL);
            console.log(audioURL);
            console.log(audio)
            model.speak(audioURL);
            return;
        }
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            console.log('ws onmessage error:', error);
            return;
        }
        if (!data) {
            return;
        }
        if (data.expression) {
            console.log('ws onmessage data.expression:', data.expression);
            model.expression(data.expression);
        }
    };
};

function addMessageToChat(message) {
    const messagesContainer = document.getElementById("messages");
    const messageElement = document.createElement("div");
    messageElement.textContent = message;
    messagesContainer.appendChild(messageElement);
}

document.getElementById("send-message").addEventListener("click", function() {
    const messageInput = document.getElementById("message-input");
    const message = messageInput.value;
    socket.send(message);
    addMessageToChat(`Вы: ${message}`);
    messageInput.value = '';
});


(async function main() {
  const app = new PIXI.Application({
    view: document.getElementById("canvas"),
    autoStart: true,
    resizeTo: window
  });

  app.stage.addChild(model4);

  model4.scale.set(0.25);
  model4.x = 200;

  bindSocket(socket, model4);
})();

