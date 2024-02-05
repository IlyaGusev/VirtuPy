// expose PIXI to window so that this plugin is able to
// reference window.PIXI.Ticker to automatically update Live2D models
window.PIXI = PIXI;

const cubism4Model = "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_greeter_t03.model3.json";
const DEFAULT_WS_ADDR = "ws://159.69.16.3:5000/ws";

function bindSocket(socket, model) {
    socket.onmessage = (event) => {
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
        if (data.model) {
            console.log('ws onmessage data.model:', data.model);
            model.setModel(data.model);
        }
        if (data.motion) {
            console.log('ws onmessage data.motion:', data.motion);
            if (typeof data.motion === 'string') {
                data.motion = {
                    group: data.motion,
                };
            }
            model.setMotion(data.motion);
        }
        if (data.expression) {
            console.log('ws onmessage data.expression:', data.expression);
            model.expression(data.expression);
        }
    };
};

const socket = new WebSocket(DEFAULT_WS_ADDR);

(async function main() {
  const app = new PIXI.Application({
    view: document.getElementById("canvas"),
    autoStart: true,
    resizeTo: window
  });

  const model4 = await PIXI.live2d.Live2DModel.from(cubism4Model);
  socket.send("!!!");
  bindSocket(socket, model4);

  app.stage.addChild(model4);

  model4.scale.set(0.25);
  model4.x = 200;
  //model4.expression(0)
})();

