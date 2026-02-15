"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// src/plugin.ts
var net = __toESM(require("net"));
var SOCKET_PATH = "/tmp/xlg-player.sock";
var XlgPlugin = class {
  constructor(port, pluginUUID, registerEvent) {
    this.port = port;
    this.pluginUUID = pluginUUID;
    this.registerEvent = registerEvent;
    this.ws = null;
    this.contexts = /* @__PURE__ */ new Map();
    this.statusInterval = null;
    this.connect();
  }
  connect() {
    this.ws = new WebSocket(`ws://127.0.0.1:${this.port}`);
    this.ws.onopen = () => this.register();
    this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
    this.ws.onclose = () => setTimeout(() => this.connect(), 1e3);
  }
  register() {
    this.ws?.send(JSON.stringify({ event: this.registerEvent, uuid: this.pluginUUID }));
    this.startStatusPolling();
  }
  handleMessage(data) {
    if (data.event === "keyDown" && data.action && data.context) {
      this.handleAction(data.action);
    }
    if (data.event === "willAppear" && data.context && data.action) {
      this.contexts.set(data.context, data.action);
    }
    if (data.event === "willDisappear" && data.context) {
      this.contexts.delete(data.context);
    }
  }
  handleAction(action) {
    const cmd = action.replace("com.xlg.player.", "");
    const commandMap = {
      "toggle": "toggle",
      "skip": "skip",
      "previous": "previous",
      "volume-up": "volume +10",
      "volume-down": "volume -10"
    };
    const socketCmd = commandMap[cmd];
    if (socketCmd)
      this.sendToPlayer(socketCmd);
  }
  sendToPlayer(command) {
    return new Promise((resolve) => {
      const client = net.createConnection(SOCKET_PATH, () => {
        client.write(command);
      });
      let data = "";
      client.on("data", (chunk) => {
        data += chunk.toString();
      });
      client.on("end", () => resolve(data.trim()));
      client.on("error", () => resolve(""));
      client.setTimeout(1e3, () => {
        client.destroy();
        resolve("");
      });
    });
  }
  startStatusPolling() {
    this.statusInterval = setInterval(async () => {
      const response = await this.sendToPlayer("status");
      if (!response)
        return;
      try {
        const status = JSON.parse(response);
        this.updateButtons(status);
      } catch {
      }
    }, 2e3);
  }
  updateButtons(status) {
    for (const [context, action] of this.contexts) {
      if (action === "com.xlg.player.toggle") {
        this.ws?.send(JSON.stringify({ event: "setState", context, payload: { state: status.playing ? 1 : 0 } }));
        if (status.title) {
          const title = status.title.length > 12 ? status.title.slice(0, 11) + "..." : status.title;
          this.ws?.send(JSON.stringify({ event: "setTitle", context, payload: { title } }));
        }
      }
    }
  }
};
var args = process.argv.slice(2);
var params = {};
for (let i = 0; i < args.length; i += 2) {
  params[args[i].replace("-", "")] = args[i + 1];
}
if (params.port && params.pluginUUID && params.registerEvent) {
  new XlgPlugin(params.port, params.pluginUUID, params.registerEvent);
}
