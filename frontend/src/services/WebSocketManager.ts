// frontend/src/services/WebSocketManager.ts
export class WebSocketManager {
    private websocket: WebSocket | null = null
    private streamWebSocket: WebSocket | null = null
    private eventListeners: Map<string, Function[]> = new Map()
    private reconnectAttempts = 0
    private maxReconnectAttempts = 5
    private reconnectDelay = 1000
  
    public connect(jobId: string): void {
      if (this.websocket) {
        this.websocket.close()
      }
  
      console.log(`📡 Connecting to WebSocket: ws://localhost:8000/ws/${jobId}`)
      this.websocket = new WebSocket(`ws://localhost:8000/ws/${jobId}`)
      
      this.websocket.onopen = () => {
        console.log('📡 WebSocket connected successfully')
        this.reconnectAttempts = 0
        this.emit('connected', { status: 'connected' })
      }
  
      this.websocket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📨 WebSocket message received:', data.type, data)
          
          // Handle different message types
          switch (data.type) {
            case 'proxy_stats':
              console.log('🔄 Proxy stats received:', data.stats || data)
              this.emit('proxy_stats', data.stats || data)
              break
            case 'decision':
              console.log('🧠 Decision received:', data.decision || data)
              this.emit('decision', data.decision || data)
              break
            case 'screenshot':
              console.log('📸 Screenshot received')
              this.emit('screenshot', data.screenshot || data)
              break
            case 'token_usage':
              console.log('📊 Token usage received:', data.token_usage || data)
              this.emit('token_usage', data.token_usage || data)
              break
            case 'page_info':
              console.log('📄 Page info received:', data)
              this.emit('page_info', data)
              break
            case 'extraction':
              console.log('🔍 Extraction update:', data)
              this.emit('extraction', data)
              break
            case 'streaming_info':
              console.log('🎥 Streaming info received:', data)
              this.emit('streaming_info', data)
              break
            case 'error':
              console.log('❌ Error received:', data)
              this.emit('error', data)
              break
            default:
              // Handle general status updates
              if (data.status) {
                console.log('📢 Status update:', data)
                this.emit('status', data)
              } else {
                console.log('📨 Unknown message type:', data.type, data)
                this.emit(data.type, data)
              }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error, event.data)
        }
      }
  
      this.websocket.onclose = (event: CloseEvent) => {
        console.log('📡 WebSocket disconnected:', event.code, event.reason)
        this.websocket = null
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`🔄 Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
          setTimeout(() => this.connect(jobId), this.reconnectDelay)
          this.reconnectDelay *= 2
        }
      }
  
      this.websocket.onerror = (error: Event) => {
        console.error('📡 WebSocket error:', error)
        this.emit('error', { error: 'WebSocket connection error' })
      }
    }
  
    public connectStream(jobId: string): void {
      if (this.streamWebSocket) {
        this.streamWebSocket.close()
      }
  
      console.log(`🎥 Connecting to Stream WebSocket: ws://localhost:8000/stream/${jobId}`)
      this.streamWebSocket = new WebSocket(`ws://localhost:8000/stream/${jobId}`)
      
      this.streamWebSocket.onopen = () => {
        console.log('🎥 Stream WebSocket connected successfully')
        this.emit('stream_connected', { status: 'connected' })
      }
  
      this.streamWebSocket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          console.log('🎥 Stream message received:', data.type)
          this.emit('stream_' + data.type, data)
        } catch (error) {
          console.error('Error parsing stream message:', error)
        }
      }
  
      this.streamWebSocket.onclose = () => {
        console.log('🎥 Stream WebSocket disconnected')
        this.streamWebSocket = null
        this.emit('stream_disconnected', { status: 'disconnected' })
      }
  
      this.streamWebSocket.onerror = (error: Event) => {
        console.error('🎥 Stream WebSocket error:', error)
        this.emit('stream_error', { error: 'Stream connection error' })
      }
    }
  
    public sendStreamMessage(message: any): void {
      if (this.streamWebSocket && this.streamWebSocket.readyState === WebSocket.OPEN) {
        this.streamWebSocket.send(JSON.stringify(message))
      } else {
        console.warn('Stream WebSocket not connected')
      }
    }
  
    public on(event: string, callback: Function): void {
      if (!this.eventListeners.has(event)) {
        this.eventListeners.set(event, [])
      }
      this.eventListeners.get(event)?.push(callback)
      console.log(`📝 Event listener added for: ${event}`)
    }
  
    private emit(event: string, data: any): void {
      const listeners = this.eventListeners.get(event) || []
      console.log(`📤 Emitting event: ${event} to ${listeners.length} listeners`)
      listeners.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error)
        }
      })
    }
  
    public disconnect(): void {
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }
    }
  
    public disconnectStream(): void {
      if (this.streamWebSocket) {
        this.streamWebSocket.close()
        this.streamWebSocket = null
      }
    }
  
    public isConnected(): boolean {
      return this.websocket !== null && this.websocket.readyState === WebSocket.OPEN
    }
  
    public isStreamConnected(): boolean {
      return this.streamWebSocket !== null && this.streamWebSocket.readyState === WebSocket.OPEN
    }
  }
  