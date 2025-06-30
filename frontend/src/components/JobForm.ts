import { WebSocketManager } from '../services/WebSocketManager'

export class JobForm {
  private wsManager: WebSocketManager
  private currentJobId: string | null = null

  constructor(wsManager: WebSocketManager) {
    this.wsManager = wsManager
  }

  public render(selector: string) {
    const container = document.querySelector(selector)
    if (!container) return

    container.innerHTML = `
      <div class="p-6">
        <div class="flex items-center space-x-3 mb-6">
          <div class="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold">🚀</span>
          </div>
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Web Automation Job</h2>
            <p class="text-sm text-gray-500">Configure your intelligent web scraping task</p>
          </div>
        </div>

        <form id="job-form-element" class="space-y-6">
          <!-- Prompt Input -->
          <div>
            <label for="prompt" class="block text-sm font-medium text-gray-700 mb-2">
              Task Description
              <span class="text-gray-400 font-normal">(mention format for auto-detection)</span>
            </label>
            <textarea 
              id="prompt" 
              rows="4"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              placeholder="Examples:&#10;• Go to https://news.ycombinator.com and save top stories as JSON&#10;• Visit firecrawl.dev pricing page and save to PDF format&#10;• Search Amazon for 'wireless headphones' and export results as CSV"
            >go to ycombinator jobs page and save the 5 job posting in txt format</textarea>
          </div>

          <!-- Format & Options -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Format Selection -->
            <div>
              <label for="format" class="block text-sm font-medium text-gray-700 mb-2">
                Output Format
              </label>
              <select id="format" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="txt">📄 Plain Text (TXT)</option>
                <option value="md">📝 Markdown (MD)</option>
                <option value="json">📊 JSON</option>
                <option value="html">🌐 HTML</option>
                <option value="csv">📈 CSV</option>
                <option value="pdf">📋 PDF</option>
              </select>
            </div>

            <!-- Options -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Options</label>
              <div class="space-y-3">
                <label class="flex items-center">
                  <input type="checkbox" id="headless" class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                  <span class="ml-2 text-sm text-gray-700">Headless Mode</span>
                </label>
                <label class="flex items-center">
                  <input type="checkbox" id="enable-streaming" checked class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                  <span class="ml-2 text-sm text-gray-700">Real-time Streaming</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Format Detection Indicator -->
          <div id="format-indicator" class="hidden p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex items-center">
              <span class="text-blue-600 mr-2">🎯</span>
              <span class="text-sm font-medium text-blue-800">Format Detection:</span>
              <span id="detected-format-text" class="ml-2 text-sm text-blue-700"></span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
            <button 
              type="button" 
              id="start-job-btn"
              class="flex-1 min-w-0 bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <span>🚀</span>
              <span>Run Universal Agent</span>
            </button>
            
            <button 
              type="button" 
              id="download-btn" 
              disabled
              class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
            >
              <span>📥</span>
              <span>Download Result</span>
            </button>
            
            <button 
              type="button" 
              id="stream-btn"
              class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 flex items-center space-x-2"
            >
              <span>🎥</span>
              <span>Create Stream</span>
            </button>
          </div>
        </form>
      </div>
    `

    this.attachEventListeners()
    this.setupDownloadListener()
  }

  private attachEventListeners() {
    // Format detection
    const promptInput = document.getElementById('prompt') as HTMLTextAreaElement
    const formatSelect = document.getElementById('format') as HTMLSelectElement
    
    const updateFormatIndicator = () => {
      const prompt = promptInput.value
      const selectedFormat = formatSelect.value
      const detectedFormat = this.detectFormatFromPrompt(prompt)
      const indicator = document.getElementById('format-indicator')
      const indicatorText = document.getElementById('detected-format-text')
      
      if (detectedFormat && detectedFormat !== selectedFormat) {
        indicator?.classList.remove('hidden')
        if (indicatorText) {
          indicatorText.textContent = `'${detectedFormat.toUpperCase()}' detected in prompt, will override dropdown selection`
        }
      } else if (detectedFormat && detectedFormat === selectedFormat) {
        indicator?.classList.remove('hidden')
        if (indicatorText) {
          indicatorText.textContent = `'${detectedFormat.toUpperCase()}' detected in prompt, matches dropdown selection`
        }
      } else {
        indicator?.classList.add('hidden')
      }
    }

    promptInput?.addEventListener('input', updateFormatIndicator)
    formatSelect?.addEventListener('change', updateFormatIndicator)

    // Job submission
    document.getElementById('start-job-btn')?.addEventListener('click', () => this.startJob())
    document.getElementById('download-btn')?.addEventListener('click', () => this.downloadResult())
    document.getElementById('stream-btn')?.addEventListener('click', () => this.createStreamingSession())
  }

  private detectFormatFromPrompt(prompt: string): string | null {
    const promptLower = prompt.toLowerCase()
    const formatPatterns = {
      'pdf': [/\bpdf\b/, /pdf format/, /save.*pdf/, /as pdf/, /to pdf/],
      'csv': [/\bcsv\b/, /csv format/, /save.*csv/, /as csv/, /to csv/],
      'json': [/\bjson\b/, /json format/, /save.*json/, /as json/, /to json/],
      'html': [/\bhtml\b/, /html format/, /save.*html/, /as html/, /to html/],
      'md': [/\bmarkdown\b/, /md format/, /save.*markdown/, /as markdown/, /to md/],
      'txt': [/\btext\b/, /txt format/, /save.*text/, /as text/, /to txt/, /plain text/]
    }
    
    for (const [format, patterns] of Object.entries(formatPatterns)) {
      for (const pattern of patterns) {
        if (pattern.test(promptLower)) {
          return format
        }
      }
    }
    return null
  }

  private async startJob() {
    const prompt = (document.getElementById('prompt') as HTMLTextAreaElement).value
    const format = (document.getElementById('format') as HTMLSelectElement).value
    const headless = (document.getElementById('headless') as HTMLInputElement).checked
    const streaming = (document.getElementById('enable-streaming') as HTMLInputElement).checked

    if (!prompt.trim()) {
      this.showNotification('Please enter a task description', 'error')
      return
    }

    const detectedFormat = this.detectFormatFromPrompt(prompt)
    const finalFormat = detectedFormat || format

    try {
      const response = await fetch('/job', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          prompt: prompt,
          format: finalFormat,
          headless: headless,
          enable_streaming: streaming
        })
      })

      const data = await response.json()
      this.currentJobId = data.job_id
      
      this.showNotification(`Job created: ${this.currentJobId} (Format: ${finalFormat.toUpperCase()})`, 'success')
      
      window.dispatchEvent(new CustomEvent('jobCreated', { 
        detail: { 
          jobId: this.currentJobId,
          streaming: streaming,  // Pass streaming flag
          format: finalFormat
        } 
      }))
      
      // Connect to WebSocket
      if (this.currentJobId) {
        this.wsManager.connect(this.currentJobId)
      }
      
    } catch (error) {
      this.showNotification(`Error: ${error}`, 'error')
    }
  }

  private async downloadResult() {
    if (!this.currentJobId) {
      this.showNotification('No job to download', 'error')
      return
    }

    try {
      const infoResponse = await fetch(`/job/${this.currentJobId}/info`)
      const jobInfo = await infoResponse.json()
      
      if (jobInfo.error) {
        this.showNotification('Job information not found', 'error')
        return
      }
      
      this.showNotification(`Downloading ${jobInfo.format?.toUpperCase() || 'TXT'} file...`, 'info')
      
      const response = await fetch(`/download/${this.currentJobId}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        
        const disposition = response.headers.get('Content-Disposition')
        let filename = `result_${this.currentJobId}.${jobInfo.extension || 'txt'}`
        if (disposition) {
          const filenameMatch = disposition.match(/filename="?([^"]+)"?/)
          if (filenameMatch) {
            filename = filenameMatch[1]
          }
        }
        
        a.download = filename
        a.click()
        window.URL.revokeObjectURL(url)
        
        this.showNotification(`✅ Downloaded: ${filename}`, 'success')
      } else {
        this.showNotification(`Download failed: ${response.statusText}`, 'error')
      }
    } catch (error) {
      this.showNotification(`Download error: ${error}`, 'error')
    }
  }

  private async createStreamingSession() {
    if (!this.currentJobId) {
      this.currentJobId = 'manual-' + Date.now()
    }

    try {
      const response = await fetch(`/streaming/create/${this.currentJobId}`, {
        method: 'POST'
      })
      
      const data = await response.json()
      
      if (data.enabled) {
        this.showNotification('Streaming session created successfully', 'success')
      } else {
        this.showNotification(`Failed to create streaming session: ${data.error}`, 'error')
      }
      
    } catch (error) {
      this.showNotification(`Error: ${error}`, 'error')
    }
  }

  private setupDownloadListener() {
    window.addEventListener('enableDownload', (event) => {
      const detail = (event as CustomEvent).detail
      const downloadBtn = document.getElementById('download-btn') as HTMLButtonElement
      if (downloadBtn) {
        downloadBtn.disabled = false
        downloadBtn.innerHTML = `<span>📥</span><span>Download ${detail.format.toUpperCase()} File</span>`
      }
    })
  }

  private showNotification(message: string, type: 'success' | 'error' | 'info') {
    window.dispatchEvent(new CustomEvent('notification', { 
      detail: { message, type } 
    }))
  }
}
