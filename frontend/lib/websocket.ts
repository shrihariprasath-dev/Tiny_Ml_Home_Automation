type MessageHandler = (data: unknown) => void;

export class SmartHomeWebSocket {
  private ws:           WebSocket | null = null;
  private handlers:     Set<MessageHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private url: string;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.info("[WS] connected");
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string);
        this.handlers.forEach((h) => h(payload));
      } catch {
        // non-JSON frame ignored
      }
    };

    this.ws.onclose = () => {
      console.info("[WS] disconnected");
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 5_000);
      }
    };

    this.ws.onerror = (err) => {
      console.error("[WS] error", err);
    };
  }

  subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.ws?.close();
  }
}

let wsInstance: SmartHomeWebSocket | null = null;

export function getWebSocket(): SmartHomeWebSocket {
  if (!wsInstance) {
    const url = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";
    wsInstance = new SmartHomeWebSocket(url);
    wsInstance.connect();
  }
  return wsInstance;
}
