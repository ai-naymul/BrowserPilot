export class StatusDisplay {
    public render(selector: string) {
      const container = document.querySelector(selector)
      if (!container) return
  
      container.innerHTML = `
        <div id="status-container" class="hidden">
          <!-- Status messages will be displayed here -->
        </div>
      `
  
      // Listen for notification events
      window.addEventListener('notification', (event) => {
        const detail = (event as CustomEvent).detail
        this.showStatus(detail.message, detail.type)
      })
    }
  
    public showStatus(message: string, type: 'success' | 'error' | 'info') {
      const container = document.getElementById('status-container')
      if (!container) return
  
      container.className = `p-4 rounded-lg mb-4 ${this.getStatusClasses(type)}`
      container.textContent = message
      container.classList.remove('hidden')
  
      // Auto-hide after 5 seconds
      setTimeout(() => {
        container.classList.add('hidden')
      }, 5000)
    }
  
    private getStatusClasses(type: string): string {
      switch (type) {
        case 'success':
          return 'bg-green-100 border border-green-200 text-green-800'
        case 'error':
          return 'bg-red-100 border border-red-200 text-red-800'
        case 'info':
        default:
          return 'bg-blue-100 border border-blue-200 text-blue-800'
      }
    }
  }
  