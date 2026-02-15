import * as net from 'net';
import WebSocket from 'ws';

const SOCKET_PATH = '/tmp/xlg-player.sock';

interface StreamDeckEvent {
  event: string;
  action?: string;
  context?: string;
  payload?: Record<string, unknown>;
}

interface PlayerStatus {
  playing: boolean;
  title: string;
  artist: string;
  volume: number;
}

class XlgPlugin {
  private ws: WebSocket | null = null;
  private contexts: Map<string, string> = new Map();
  private statusInterval: NodeJS.Timeout | null = null;

  constructor(private port: string, private pluginUUID: string, private registerEvent: string) {
    this.connect();
  }

  private connect(): void {
    this.ws = new WebSocket(`ws://127.0.0.1:${this.port}`);
    this.ws.on('open', () => this.register());
    this.ws.on('message', (data) => this.handleMessage(JSON.parse(data.toString())));
    this.ws.on('close', () => setTimeout(() => this.connect(), 1000));
  }

  private register(): void {
    this.ws?.send(JSON.stringify({ event: this.registerEvent, uuid: this.pluginUUID }));
    this.startStatusPolling();
  }

  private handleMessage(data: StreamDeckEvent): void {
    if (data.event === 'keyDown' && data.action && data.context) {
      this.handleAction(data.action);
    }
    if (data.event === 'willAppear' && data.context && data.action) {
      this.contexts.set(data.context, data.action);
    }
    if (data.event === 'willDisappear' && data.context) {
      this.contexts.delete(data.context);
    }
  }

  private handleAction(action: string): void {
    const cmd = action.replace('com.xlg.player.', '');
    const commandMap: Record<string, string> = {
      'toggle': 'toggle',
      'skip': 'skip',
      'previous': 'previous',
      'volume-up': 'volume +10',
      'volume-down': 'volume -10',
      'favorite': 'favorite'
    };
    const socketCmd = commandMap[cmd];
    if (socketCmd) this.sendToPlayer(socketCmd);
  }

  private sendToPlayer(command: string): Promise<string> {
    return new Promise((resolve) => {
      const client = net.createConnection(SOCKET_PATH, () => {
        client.write(command);
      });
      let data = '';
      client.on('data', (chunk) => { data += chunk.toString(); });
      client.on('end', () => resolve(data.trim()));
      client.on('error', () => resolve(''));
      client.setTimeout(1000, () => { client.destroy(); resolve(''); });
    });
  }

  private startStatusPolling(): void {
    this.statusInterval = setInterval(async () => {
      const response = await this.sendToPlayer('status');
      if (!response) return;
      try {
        const status: PlayerStatus = JSON.parse(response);
        this.updateButtons(status);
      } catch { /* ignore parse errors */ }
    }, 2000);
  }

  private updateButtons(status: PlayerStatus): void {
    for (const [context, action] of this.contexts) {
      if (action === 'com.xlg.player.toggle') {
        this.ws?.send(JSON.stringify({ event: 'setState', context, payload: { state: status.playing ? 1 : 0 } }));
        if (status.title) {
          const title = status.title.length > 12 ? status.title.slice(0, 11) + '...' : status.title;
          this.ws?.send(JSON.stringify({ event: 'setTitle', context, payload: { title } }));
        }
      }
    }
  }
}

const args = process.argv.slice(2);
const params: Record<string, string> = {};
for (let i = 0; i < args.length; i += 2) {
  params[args[i].replace('-', '')] = args[i + 1];
}

if (params.port && params.pluginUUID && params.registerEvent) {
  new XlgPlugin(params.port, params.pluginUUID, params.registerEvent);
}
