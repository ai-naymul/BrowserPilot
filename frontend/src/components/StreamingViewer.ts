import { WebSocketManager } from '../services/WebSocketManager'

export class StreamingViewer {
  private wsManager: WebSocketManager
  private streamStats = { frameCount: 0, startTime: null as number | null, lastFrameTime: null as number | null }
  private currentJobId: string | null = null

  constructor(wsManager: WebSocketManager) {
    this.wsManager = wsManager
    this.setupStreamListeners()
  }

  private setupStreamListeners(): void {
    // Listen for stream events from WebSocketManager
    this.wsManager.on('stream_connected', () => {
      this.updateStreamStatus('connected')
      this.streamStats.startTime = Date.now()
      this.streamStats.frameCount = 0
    })

    this.wsManager.on('stream_disconnected', () => {
      this.updateStreamStatus('disconnected')
    })

    this.wsManager.on('stream_frame', (data: any) => {
      this.displayFrame(data.data)
      this.updateStreamStats()
    })

    this.wsManager.on('stream_error', (data: any) => {
      this.showNotification(`Stream error: ${data.error}`, 'error')
      this.updateStreamStatus('disconnected')
    })
  }

  public setJobId(jobId: string): void {
    this.currentJobId = jobId
    console.log(`🎥 StreamingViewer job ID set to: ${jobId}`)
  }

  public render(selector: string): void {
    const container = document.querySelector(selector)
    if (!container) return

    container.innerHTML = `
      <div class="p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold">🎥</span>
            </div>
            <div>
              <h2 class="text-lg font-semibold text-gray-900">Real-time Browser View</h2>
              <p class="text-sm text-gray-500">Live browser streaming with interaction</p>
            </div>
          </div>
          
          <div class="flex items-center space-x-2">
            <div id="stream-status" class="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
              Disconnected
            </div>
            <span id="stream-fps" class="text-xs text-gray-500">0 FPS</span>
          </div>
        </div>

        <div id="stream-container" class="hidden">
          <div class="relative bg-black rounded-lg overflow-hidden border border-gray-200 shadow-sm">
            <img id="stream-frame" class="w-full h-auto cursor-pointer" alt="Browser Stream">
            
            <!-- Stream Controls -->
            <div class="absolute bottom-4 left-4 right-4">
              <div class="bg-black bg-opacity-70 backdrop-blur-sm rounded-lg p-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <button id="connect-stream" class="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600 transition-colors">
                      🔗 Connect
                    </button>
                    <button id="disconnect-stream" class="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600 transition-colors">
                      🔌 Disconnect
                    </button>
                    <button id="take-screenshot" class="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors">
                      📸 Screenshot
                    </button>
                  </div>
                  
                  <div class="flex items-center space-x-2 text-white text-sm">
                    <span>Quality:</span>
                    <select id="stream-quality" class="bg-gray-700 text-white rounded px-2 py-1 text-xs">
                      <option value="60">Low (60%)</option>
                      <option value="80" selected>Medium (80%)</option>
                      <option value="100">High (100%)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div id="stream-placeholder" class="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <div class="w-16 h-16 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
            <span class="text-gray-400 text-2xl">🎥</span>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Browser Streaming</h3>
          <p class="text-gray-500 mb-4">Enable streaming to view browser in real-time</p>
          <button id="enable-streaming-btn" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
            Enable Streaming
          </button>
        </div>
      </div>
    `

    this.attachEventListeners()
  }

  private attachEventListeners(): void {
    document.getElementById('connect-stream')?.addEventListener('click', () => this.connectStream())
    document.getElementById('disconnect-stream')?.addEventListener('click', () => this.disconnectStream())
    document.getElementById('take-screenshot')?.addEventListener('click', () => this.takeScreenshot())
    document.getElementById('enable-streaming-btn')?.addEventListener('click', () => this.enableStreaming())
    document.getElementById('stream-quality')?.addEventListener('change', () => this.updateStreamQuality())

    // Stream frame interaction
    document.getElementById('stream-frame')?.addEventListener('click', (e) => this.handleStreamClick(e))
  }

  private connectStream(): void {
    if (!this.currentJobId) {
      this.showNotification('No job ID available for streaming', 'error')
      return
    }

    console.log(`🎥 Connecting to stream for job: ${this.currentJobId}`)
    this.updateStreamStatus('connecting')
    this.wsManager.connectStream(this.currentJobId)
  }

  private disconnectStream(): void {
    console.log('🎥 Disconnecting stream')
    this.wsManager.disconnectStream()
    this.updateStreamStatus('disconnected')
  }

  private displayFrame(base64Data: string): void {
    const streamFrame = document.getElementById('stream-frame') as HTMLImageElement
    if (streamFrame) {
      streamFrame.src = `data:image/jpeg;base64,${base64Data}`
    }
  }

  private updateStreamStats(): void {
    this.streamStats.frameCount++
    this.streamStats.lastFrameTime = Date.now()
    
    if (this.streamStats.startTime) {
      const elapsed = (Date.now() - this.streamStats.startTime) / 1000
      const fps = Math.round(this.streamStats.frameCount / elapsed)
      const fpsElement = document.getElementById('stream-fps')
      if (fpsElement) {
        fpsElement.textContent = `${fps} FPS`
      }
    }
  }

  private updateStreamStatus(status: 'connected' | 'disconnected' | 'connecting'): void {
    const statusElement = document.getElementById('stream-status')
    if (!statusElement) return

    statusElement.className = `px-3 py-1 rounded-full text-xs font-medium`
    statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1)

    switch (status) {
      case 'connected':
        statusElement.classList.add('bg-green-100', 'text-green-800')
        break
      case 'disconnected':
        statusElement.classList.add('bg-red-100', 'text-red-800')
        break
      case 'connecting':
        statusElement.classList.add('bg-yellow-100', 'text-yellow-800')
        break
    }
  }

  private handleStreamClick(e: Event): void {
    if (!this.wsManager.isStreamConnected()) {
      return
    }

    const mouseEvent = e as MouseEvent
    const target = mouseEvent.target as HTMLImageElement
    const rect = target.getBoundingClientRect()
    
    const x = Math.round((mouseEvent.clientX - rect.left) * (1280 / rect.width))
    const y = Math.round((mouseEvent.clientY - rect.top) * (800 / rect.height))

    // Send mouse click
    this.wsManager.sendStreamMessage({
      type: 'mouse',
      eventType: 'mousePressed',
      x: x,
      y: y,
      button: 'left',
      clickCount: 1
    })

    setTimeout(() => {
      this.wsManager.sendStreamMessage({
        type: 'mouse',
        eventType: 'mouseReleased',
        x: x,
        y: y,
        button: 'left'
      })
    }, 100)
  }

  private takeScreenshot(): void {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = document.getElementById('stream-frame') as HTMLImageElement
    
    if (!ctx || !img) return

    canvas.width = img.naturalWidth || img.width
    canvas.height = img.naturalHeight || img.height
    ctx.drawImage(img, 0, 0)
    
    const link = document.createElement('a')
    link.download = `screenshot_${Date.now()}.png`
    link.href = canvas.toDataURL()
    link.click()

    this.showNotification('Screenshot saved', 'success')
  }

  private enableStreaming(): void {
    const container = document.getElementById('stream-container')
    const placeholder = document.getElementById('stream-placeholder')
    
    container?.classList.remove('hidden')
    placeholder?.classList.add('hidden')

    // Auto-connect if we have a job ID
    if (this.currentJobId) {
      setTimeout(() => this.connectStream(), 1000)
    }
  }

  private updateStreamQuality(): void {
    this.showNotification('Quality change will take effect on next connection', 'info')
  }

  private showNotification(message: string, type: 'success' | 'error' | 'info'): void {
    window.dispatchEvent(new CustomEvent('notification', { 
      detail: { message, type } 
    }))
  }

  // Public methods
  public showStreamContainer(): void {
    const container = document.getElementById('stream-container')
    const placeholder = document.getElementById('stream-placeholder')
    
    container?.classList.remove('hidden')
    placeholder?.classList.add('hidden')
  }

  public isConnected(): boolean {
    return this.wsManager.isStreamConnected()
  }
}
