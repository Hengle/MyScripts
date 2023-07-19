!function(e,t){if("object"==typeof exports&&"object"==typeof module)module.exports=t();else if("function"==typeof define&&define.amd)define([],t);else{var n=t();for(var o in n)("object"==typeof exports?exports:e)[o]=n[o]}}(self,(()=>(()=>{"use strict";var e={};e.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),e.r=e=>{"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})};var t={};function n(){return n=Object.assign||function(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var o in n)Object.prototype.hasOwnProperty.call(n,o)&&(e[o]=n[o])}return e},n.apply(this,arguments)}e.r(t);const o={c:"c",s:"s",a:"a",m:"m",ctrl:"c",control:"c",shift:"s",alt:"a",meta:"m",ctrlcmd:navigator.userAgent.includes("Macintosh")?"m":"c"},i={arrowup:"up",arrowdown:"down",arrowleft:"left",arrowright:"right",enter:"cr",escape:"esc"," ":"space"};function r(e,t,n=!1){const{c:o,s:r,a:s,m:c}=t;return(!n||e.length>1)&&(e=e.toLowerCase()),[c&&"m",o&&"c",r&&"s",s&&"a",e=i[e]||e].filter(Boolean).join("-")}function s(e,t=!1){const n=e.split("-"),i=n.pop(),s={};for(const e of n){const t=o[e.toLowerCase()];if(!t)throw new Error(`Unknown modifier key: ${e}`);s[t]=!0}return r(i,s,t)}class c{constructor(){this.children=new Map,this.shortcuts=new Set}add(e,t){let n=this;for(const t of e){let e=n.children.get(t);e||(e=new c,n.children.set(t,e)),n=e}n.shortcuts.add(t)}get(e){let t=this;for(const n of e)if(t=t.children.get(n),!t)return null;return t}remove(e,t){let n=this;const o=[n];for(const t of e){if(n=n.children.get(t),!n)return;o.push(n)}t?n.shortcuts.delete(t):n.shortcuts.clear();let i=o.length-1;for(;i>1&&(n=o[i],!n.shortcuts.size&&!n.children.size);){o[i-1].children.delete(e[i-1]),i-=1}}}class l{constructor(){this._context={},this._conditionData={},this._dataCI=[],this._dataCS=[],this._rootCI=new c,this._rootCS=new c,this.options={sequenceTimeout:500},this._reset=()=>{this._curCI=null,this._curCS=null,this._resetTimer()},this.handleKey=e=>{if(!e.key||e.key.length>1&&o[e.key.toLowerCase()])return;this._resetTimer();const t=r(e.key,{c:e.ctrlKey,a:e.altKey,m:e.metaKey},!0),n=r(e.key,{c:e.ctrlKey,s:e.shiftKey,a:e.altKey,m:e.metaKey});this.handleKeyOnce(t,n,!1)&&(e.preventDefault(),this._reset()),this._timer=setTimeout(this._reset,this.options.sequenceTimeout)}}_resetTimer(){this._timer&&(clearTimeout(this._timer),this._timer=null)}_addCondition(e){let t=this._conditionData[e];if(!t){const n=function(e){return e.split("&&").map((e=>{if(e=e.trim())return"!"===e[0]?{not:!0,field:e.slice(1).trim()}:{not:!1,field:e}})).filter(Boolean)}(e);t={count:0,value:n,result:this._evalCondition(n)},this._conditionData[e]=t}t.count+=1}_removeCondition(e){const t=this._conditionData[e];t&&(t.count-=1,t.count||delete this._conditionData[e])}_evalCondition(e){return e.every((e=>{let t=this._context[e.field];return e.not&&(t=!t),t}))}_checkShortcut(e){const t=e.condition&&this._conditionData[e.condition],n=!t||t.result;e.enabled!==n&&(e.enabled=n,this._enableShortcut(e))}_enableShortcut(e){const t=e.caseSensitive?this._rootCS:this._rootCI;e.enabled?t.add(e.sequence,e):t.remove(e.sequence,e)}enable(){this.disable(),document.addEventListener("keydown",this.handleKey)}disable(){document.removeEventListener("keydown",this.handleKey)}register(e,t,o){const{caseSensitive:i,condition:r}=n({caseSensitive:!1},o),c=function(e,t){return e.split(" ").map((e=>s(e,t)))}(e,i),l=i?this._dataCS:this._dataCI,a={sequence:c,condition:r,callback:t,enabled:!1,caseSensitive:i};return r&&this._addCondition(r),this._checkShortcut(a),l.push(a),()=>{const e=l.indexOf(a);e>=0&&(l.splice(e,1),r&&this._removeCondition(r),a.enabled=!1,this._enableShortcut(a))}}setContext(e,t){this._context[e]=t;for(const e of Object.values(this._conditionData))e.result=this._evalCondition(e.value);for(const e of[this._dataCS,this._dataCI])for(const t of e)this._checkShortcut(t)}handleKeyOnce(e,t,n){var o,i;let r=this._curCS,s=this._curCI;(n||!r&&!s)&&(n=!0,r=this._rootCS,s=this._rootCI),r&&(r=r.get([e])),s&&(s=s.get([t]));const c=[...s?s.shortcuts:[],...r?r.shortcuts:[]].reverse();if(this._curCS=r,this._curCI=s,!(n||c.length||null!=(o=r)&&o.children.size||null!=(i=s)&&i.children.size))return this.handleKeyOnce(e,t,!0);for(const e of c){try{e.callback()}catch(e){}return!0}}}let a;function d(){return a||(a=new l,a.enable()),a}const u="1px solid lightgray",h=!1,m="8pt",f="0.8",p=window||e.g;function y(){let e=document.getElementById("userscriptlib-container");if(e)return e;{const t=function(){const e=document.createElement("div");return e.style.opacity=f,e.style.left="0",e.style.position="fixed",e.style.top="0",e.style.width="150px",e.style.zIndex="9999",document.body.appendChild(e),e}();let n=h;function o(){i.style.display=n?"none":"block"}!function({panel:e,onClick:t}){const n=document.createElement("div");n.style.backgroundColor="lightgray",n.style.height="12px",e.appendChild(n),n.addEventListener("mousedown",(n=>{n.preventDefault();let o=n.clientX,i=n.clientY,r=!1;const s=t=>{t.preventDefault();const n=o-t.clientX,s=i-t.clientY;o=t.clientX,i=t.clientY,e.style.top=e.offsetTop-s+"px",e.style.left=e.offsetLeft-n+"px",r=!0},c=()=>{document.removeEventListener("mouseup",c),document.removeEventListener("mousemove",s),!r&&t&&t()};document.addEventListener("mouseup",c),document.addEventListener("mousemove",s)}))}({panel:t,onClick:()=>{n=!n,o()}});const i=document.createElement("div");return t.appendChild(i),o(),e=function(e,t){return e=document.createElement("div"),e.id="userscriptlib-container",t.appendChild(e),e}(e,i),function(e){const t=document.createElement("textarea");t.id="userscriptlib-log-pane",t.readOnly=!0,t.rows=5,t.style.all="revert",t.style.boxSizing="border-box",t.style.fontSize=m,t.style.resize="none",t.style.width="100%",t.style.border=u,e.appendChild(t)}(i),e}}function v(e){y();const t=document.getElementById("userscriptlib-log-pane");""!==t.value?t.value+="\n"+e:t.value=e,t.scrollTop=t.scrollHeight}function b(e){const t=()=>{const t=e();return t&&t instanceof HTMLElement&&(t.scrollIntoView(),t.style.backgroundColor="#FDFF47"),t};return new Promise((e=>{const n=t();e(n);const o=new MutationObserver((n=>{const i=t();i&&(e(i),o.disconnect())}));o.observe(document.body,{childList:!0,subtree:!0})}))}function w(e=window.document){if(e.body!==e.activeElement&&"IFRAME"!=e.activeElement.tagName)return e.activeElement;for(var t=e.getElementsByTagName("iframe"),n=0;n<t.length;n++){var o=w(t[n].contentWindow.document);if(null!==o)return o}return null}return p.addButton=(e,t,n)=>{const o=document.createElement("button");o.style.backgroundColor="white",o.style.border=u,o.style.color="black",o.style.display="block",o.style.fontSize=m,o.style.margin="0",o.style.padding="0px 10px",o.style.width="100%",o.textContent=e,n&&(o.textContent+=` (${n})`),o.onclick=t,y().appendChild(o),n&&((...e)=>{d().register(...e)})(n,t)},p.addText=(e,{color:t="black"})=>{const n=document.createElement("div");n.textContent=e,n.style.color=t,y().appendChild(n)},p.findElementByXPath=e=>document.evaluate(e,document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue,p.findElementBySelector=e=>document.querySelector(e),p.findElementByText=e=>findElementByXPath(`//*[text() = '${e}']`),p.findElementByPartialText=e=>findElementByXPath(`//*[contains(text(),'${e}')]`),p.waitForSelector=e=>b((()=>document.querySelector(e))),p.waitForSelectorAll=e=>b((()=>document.querySelectorAll(e))),p.waitForText=e=>b((()=>findElementByText(e))),p.waitForPartialText=e=>b((()=>findElementByPartialText(e))),p.waitForXPath=e=>b((()=>findElementByXPath(e))),p.saveAsFile=(e,t,n="text/plain")=>{var o=new Blob([e],{type:n});if(window.navigator.msSaveOrOpenBlob)window.navigator.msSaveOrOpenBlob(o,t);else{var i=document.createElement("a"),r=URL.createObjectURL(o);i.href=r,i.download=t,document.body.appendChild(i),i.click(),setTimeout((function(){document.body.removeChild(i),window.URL.revokeObjectURL(r)}),0)}},p.download=(e,t)=>{fetch(e).then((e=>e.blob())).then((n=>{const o=document.createElement("a");o.href=URL.createObjectURL(n),o.download=t||e.split("/").pop().split("?")[0],o.click()})).catch(console.error)},p.exec=e=>{if(GM_xmlhttpRequest)return new Promise((t=>{GM_xmlhttpRequest({method:"POST",url:"http://127.0.0.1:4312/exec",responseType:"text",data:JSON.stringify({args:e}),headers:{"Content-Type":"application/json; charset=UTF-8"},onload:e=>{t(e.responseText)}})}));alert('ERROR: please make sure "@grant GM_xmlhttpRequest" is present.')},p.openInNewWindow=e=>{window.open(e,"_blank")},p.getSelectedText=()=>window.getSelection().toString().trim().replace(/ /g,"_"),p.sendText=e=>{const t=w();if(t)if(t instanceof HTMLInputElement||t instanceof HTMLTextAreaElement){const[n,o]=[t.selectionStart,t.selectionEnd];t.setRangeText(e,n,o,"end")}else for(let n=0;n<e.length;n++){const o=new KeyboardEvent("keypress",{bubbles:!0,cancelable:!0,keyCode:e.charCodeAt(n)});t.dispatchEvent(o)}},p.click=e=>{const t=function(e,t,n,o){e.dispatchEvent(new MouseEvent(t,{bubbles:!0,cancelable:!0,clientX:n,clientY:o,button:0}))};var n=e.getBoundingClientRect(),o=n.left+(n.right-n.left)/2,i=n.top+(n.bottom-n.top)/2;t(e,"mousedown",o,i),t(e,"mouseup",o,i),t(e,"click",o,i)},p.sendKey=(e,t)=>{const n="string"==typeof t?"key"+t:"keydown",o=document.createEvent("HTMLEvents");o.initEvent(n,!0,!1),o.keyCode=e,document.dispatchEvent(o)},p.sleep=(e,t)=>{const n=Date.now();function o(){const o=t/1e3-((Date.now()-n)/1e3|0),r=o/60|0,s=o%60|0;o<=0?(clearInterval(i),e()):v(`${r<10?"0"+r:r}:${s<10?"0"+s:s}`)}o();const i=setInterval(o,1e3)},p.logd=v,t})()));