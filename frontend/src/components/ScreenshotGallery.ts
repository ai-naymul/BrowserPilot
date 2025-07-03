export class ScreenshotGallery {
    private screenshots: string[] = []
  
    public render(selector: string): void {
      const container = document.querySelector(selector)
      if (!container) return
  
      container.innerHTML = `
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-lg flex items-center justify-center">
                <span class="text-white font-bold">📸</span>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-gray-900">Screenshots</h2>
                <p class="text-sm text-gray-500">Captured browser states during automation</p>
              </div>
            </div>
            
            <div class="flex items-center space-x-2">
              <span id="screenshot-count" class="text-sm text-gray-500">0 screenshots</span>
              <button id="clear-screenshots" class="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors">
                Clear
              </button>
            </div>
          </div>
  
          <div id="screenshots-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
            <div class="col-span-full text-gray-500 text-center py-8">
              No screenshots captured yet. Screenshots will appear here as the agent runs.
            </div>
          </div>
        </div>
      `
  
      this.attachEventListeners()
    }
  
    private attachEventListeners(): void {
      document.getElementById('clear-screenshots')?.addEventListener('click', () => this.clearScreenshots())
    }
  
    public addScreenshot(screenshot: string): void {
      const container = document.getElementById('screenshots-container')
      if (!container) return
  
      // Remove empty state if present
      if (container.children.length === 1 && container.children[0].classList.contains('col-span-full')) {
        container.innerHTML = ''
      }
  
      this.screenshots.push(screenshot)
  
      const screenshotDiv = document.createElement('div')
      screenshotDiv.className = 'relative group cursor-pointer'
      
      const timestamp = new Date().toLocaleTimeString()
      screenshotDiv.innerHTML = `
        <img src="data:image/png;base64,${screenshot}" 
             class="w-full h-32 object-cover rounded-lg border border-gray-200 hover:border-blue-300 transition-colors" 
             alt="Screenshot ${this.screenshots.length}">
        <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity rounded-lg"></div>
        <div class="absolute bottom-2 left-2 right-2">
          <div class="bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
            Screenshot ${this.screenshots.length} - ${timestamp}
          </div>
        </div>
      `
  
      screenshotDiv.addEventListener('click', () => {
        const newWindow = window.open()
        if (newWindow) {
          newWindow.document.write(`
            <html>
              <head><title>Screenshot ${this.screenshots.length}</title></head>
              <body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;">
                <img src="data:image/png;base64,${screenshot}" style="max-width:100%;max-height:100%;object-fit:contain;">
              </body>
            </html>
          `)
        }
      })
  
      container.appendChild(screenshotDiv)
      this.updateScreenshotCount()
  
      console.log('✅ Screenshot added to UI')
    }
  
    private updateScreenshotCount(): void {
      const countElement = document.getElementById('screenshot-count')
      if (countElement) {
        const count = this.screenshots.length
        countElement.textContent = `${count} screenshot${count !== 1 ? 's' : ''}`
      }
    }
  
    public clearScreenshots(): void {
      const container = document.getElementById('screenshots-container')
      if (!container) return
  
      this.screenshots = []
      container.innerHTML = `
        <div class="col-span-full text-gray-500 text-center py-8">
          No screenshots captured yet. Screenshots will appear here as the agent runs.
        </div>
      `
      this.updateScreenshotCount()
    }
  }
  