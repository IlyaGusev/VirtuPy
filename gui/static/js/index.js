// expose PIXI to window so that this plugin is able to
// reference window.PIXI.Ticker to automatically update Live2D models
window.PIXI = PIXI;

const cubism4Model = "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_greeter_t03.model3.json";

(async function main() {
  const app = new PIXI.Application({
    view: document.getElementById("canvas"),
    autoStart: true,
    resizeTo: window
  });

  const model4 = await PIXI.live2d.Live2DModel.from(cubism4Model);

  app.stage.addChild(model4);

  model4.scale.set(0.25);
  model4.x = 100;
})();

