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
          this.emit(data.type, data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
  
      this.websocket.onclose = (event: CloseEvent) => {
        console.log('📡 WebSocket disconnected:', event.code, event.reason)
        this.websocket = null
        
        // Attempt reconnection
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`🔄 Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
          setTimeout(() => this.connect(jobId), this.reconnectDelay)
          this.reconnectDelay *= 2 // Exponential backoff
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
    }
  
    public off(event: string, callback: Function): void {
      const listeners = this.eventListeners.get(event)
      if (listeners) {
        const index = listeners.indexOf(callback)
        if (index !== -1) {
          listeners.splice(index, 1)
        }
      }
    }
  
    private emit(event: string, data: any): void {
      const listeners = this.eventListeners.get(event) || []
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
  