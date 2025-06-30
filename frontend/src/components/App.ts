// frontend/src/components/App.ts
import { JobForm } from './JobForm'
import { StatusDisplay } from './StatusDisplay'
import { TokenUsage } from './TokenUsage'
import { DecisionLog } from './DecisionLog'
import { ScreenshotGallery } from './ScreenshotGallery'
import { StreamingViewer } from './StreamingViewer'
import { ProxyStats } from './ProxyStats'
import { WebSocketManager } from '../services/WebSocketManager'

interface ComponentData {
  [key: string]: any
}

export class App {
  private wsManager: WebSocketManager
  private components!: {
    jobForm: JobForm
    statusDisplay: StatusDisplay
    tokenUsage: TokenUsage
    decisionLog: DecisionLog
    screenshotGallery: ScreenshotGallery
    streamingViewer: StreamingViewer
    proxyStats: ProxyStats
  }

  constructor() {
    this.wsManager = new WebSocketManager()
    this.initializeComponents()
  }

  private initializeComponents() {
    this.components = {
      jobForm: new JobForm(this.wsManager),
      statusDisplay: new StatusDisplay(),
      tokenUsage: new TokenUsage(),
      decisionLog: new DecisionLog(),
      screenshotGallery: new ScreenshotGallery(),
      streamingViewer: new StreamingViewer(this.wsManager),
      proxyStats: new ProxyStats()
    }

    console.log('🔧 Setting up WebSocket event listeners...')

    // Connect WebSocket events to components with detailed logging
    this.wsManager.on('decision', (data: ComponentData) => {
        console.log('🧠 App received decision:', data)
        
        // Handle the decision
        if (data.decision) {
          this.components.decisionLog.addDecision(data.decision)
          
          // Extract token usage from decision if present
          if (data.decision.token_usage) {
            console.log('📊 Extracting token usage from decision:', data.decision.token_usage)
            this.components.tokenUsage.updateUsage(data.decision.token_usage)
          }
        } else {
          this.components.decisionLog.addDecision(data)
          
          // Check for token usage in the data itself
          if (data.token_usage) {
            console.log('📊 Extracting token usage from data:', data.token_usage)
            this.components.tokenUsage.updateUsage(data.token_usage)
          }
        }
    })

    this.wsManager.on('screenshot', (data: ComponentData) => {
      console.log('📸 App received screenshot')
      const screenshot = data.screenshot || data
      if (typeof screenshot === 'string') {
        this.components.screenshotGallery.addScreenshot(screenshot)
      } else {
        console.warn('Invalid screenshot data type:', typeof screenshot)
      }
    })

    this.wsManager.on('proxy_stats', (data: ComponentData) => {
      console.log('🔄 App received proxy stats:', data)
      // Handle both direct stats and nested stats
      const stats = data.stats || data
      this.components.proxyStats.updateStats(stats)
    })

    this.wsManager.on('token_usage', (data: ComponentData) => {
      console.log('📊 App received token usage:', data)
      const usage = data.token_usage || data
      this.components.tokenUsage.updateUsage(usage)
    })

    // Handle page info updates
    this.wsManager.on('page_info', (data: ComponentData) => {
      console.log('📄 App received page info:', data)
      this.showStatus(`Step ${data.step}: ${data.url} (${data.interactive_elements} elements) [${data.format?.toUpperCase() || 'TXT'}]`, 'info')
    })

    // Handle extraction status
    this.wsManager.on('extraction', (data: ComponentData) => {
      console.log('🔍 App received extraction:', data)
      if (data.status === 'starting') {
        this.showStatus(`Starting extraction (attempt ${data.attempt}) in ${data.format?.toUpperCase() || 'TXT'} format...`, 'info')
      } else if (data.status === 'completed') {
        this.showStatus(`✅ Extraction completed! Format: ${data.format?.toUpperCase() || 'TXT'}`, 'success')
        this.enableDownloadButton(data.format || 'TXT')
      }
    })

    // Handle streaming updates
    this.wsManager.on('streaming_info', (data: ComponentData) => {
      console.log('🎥 App received streaming info:', data)
      if (data.streaming?.enabled) {
        this.showStatus('Streaming available', 'success')
        this.components.streamingViewer.showStreamContainer()
      }
    })

    // Handle general status
    this.wsManager.on('status', (data: ComponentData) => {
      console.log('📢 App received status:', data)
      if (data.status === 'started') {
        this.showStatus(`Status: ${data.status} | Format: ${data.detected_format?.toUpperCase() || 'TXT'}`, 'info')
      } else if (data.status === 'finished') {
        this.showStatus(`Status: ${data.status} | Final format: ${data.final_format?.toUpperCase() || 'TXT'}`, 'success')
        this.enableDownloadButton(data.final_format || 'TXT')
      }
    })

    // Handle errors
    this.wsManager.on('error', (data: ComponentData) => {
      console.log('❌ App received error:', data)
      this.showStatus(`❌ ${data.message || data.error || 'Unknown error'}`, 'error')
      if (data.proxy_stats) {
        this.components.proxyStats.updateStats(data.proxy_stats)
      }
    })

    // Listen for connection events
    this.wsManager.on('connected', () => {
      console.log('✅ App received WebSocket connected event')
      this.showStatus('Connected to server', 'success')
    })

    console.log('✅ WebSocket event listeners set up complete')
  }

  private showStatus(message: string, type: 'success' | 'error' | 'info') {
    console.log(`📢 Showing status: [${type}] ${message}`)
    this.components.statusDisplay.showStatus(message, type)
  }

  private enableDownloadButton(format: string) {
    console.log(`📥 Enabling download button for format: ${format}`)
    window.dispatchEvent(new CustomEvent('enableDownload', { 
      detail: { format } 
    }))
  }

  public render() {
    document.body.innerHTML = `
      <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b border-gray-200">
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span class="text-white font-bold text-sm">🤖</span>
                </div>
                <h1 class="text-xl font-semibold text-gray-900">Universal Web Agent</h1>
              </div>
              <div class="flex items-center space-x-4">
                <div id="proxy-indicator" class="hidden"></div>
                <div id="status-indicator" class="w-3 h-3 bg-gray-300 rounded-full"></div>
              </div>
            </div>
          </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <!-- Control Panel -->
          <div class="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
            <!-- Job Configuration -->
            <div class="xl:col-span-2">
              <div id="job-form" class="bg-white rounded-xl shadow-sm border border-gray-200"></div>
            </div>
            
            <!-- Quick Stats -->
            <div class="space-y-6">
              <div id="token-usage" class="bg-white rounded-xl shadow-sm border border-gray-200"></div>
              <div id="proxy-stats" class="bg-white rounded-xl shadow-sm border border-gray-200"></div>
            </div>
          </div>

          <!-- Status Display -->
          <div id="status-display" class="mb-8"></div>

          <!-- Real-time Views -->
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
            <!-- Browser Streaming -->
            <div id="streaming-viewer" class="bg-white rounded-xl shadow-sm border border-gray-200"></div>
            
            <!-- Decision Log -->
            <div id="decision-log" class="bg-white rounded-xl shadow-sm border border-gray-200"></div>
          </div>

          <!-- Screenshot Gallery -->
          <div id="screenshot-gallery" class="bg-white rounded-xl shadow-sm border border-gray-200"></div>
        </main>
      </div>
    `

    // Render components
    console.log('🎨 Rendering components...')
    this.components.jobForm.render('#job-form')
    this.components.statusDisplay.render('#status-display')
    this.components.tokenUsage.render('#token-usage')
    this.components.decisionLog.render('#decision-log')
    this.components.screenshotGallery.render('#screenshot-gallery')
    this.components.streamingViewer.render('#streaming-viewer')
    this.components.proxyStats.render('#proxy-stats')

    // Set up job creation event handling
    window.addEventListener('jobCreated', (event) => {
      const detail = (event as CustomEvent).detail
      console.log('🚀 Job created event received:', detail)
      this.components.streamingViewer.setJobId(detail.jobId)
      
      // Auto-enable streaming if requested
      if (detail.streaming) {
        setTimeout(() => {
          this.components.streamingViewer.showStreamContainer()
        }, 2000)
      }
    })

    console.log('✅ App rendering complete')
  }
}
