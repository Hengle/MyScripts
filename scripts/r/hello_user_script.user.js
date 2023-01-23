// ==UserScript==
// @name        HelloUserScript
// @namespace   Violentmonkey Scripts
// @match       https://www.google.com/*
// @grant       none
// @version     1.0
// @author      -
// @description 9/10/2022, 2:52:23 PM
// @require https://cdn.jsdelivr.net/combine/npm/@violentmonkey/dom@2,npm/@violentmonkey/ui@0.7
// @require https://cdn.jsdelivr.net/npm/@violentmonkey/shortcut@1
// @require ../../jslib/_userscript.js
// ==/UserScript==

VM.shortcut.register("c-i", () => {
  alert("c-i pressed");
});

(function createPanel() {
  let btn = document.createElement("button");
  btn.innerHTML = "Click Me";
  btn.onclick = function () {
    findText("Terms");
  };

  const panel = VM.getPanel({
    content: btn,
  });
  panel.wrapper.style.top = "0";
  panel.setMovable(true);
  panel.show();
})();
