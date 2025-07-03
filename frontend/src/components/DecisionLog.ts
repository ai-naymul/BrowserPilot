export class DecisionLog {
    public render(selector: string): void {
      const container = document.querySelector(selector)
      if (!container) return
  
      container.innerHTML = `
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-gradient-to-r from-indigo-400 to-purple-500 rounded-lg flex items-center justify-center">
                <span class="text-white font-bold">🧠</span>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-gray-900">Recent Decisions</h2>
                <p class="text-sm text-gray-500">AI agent reasoning and actions</p>
              </div>
            </div>
            
            <button id="clear-decisions" class="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors">
              Clear
            </button>
          </div>
  
          <div id="decisions-container" class="bg-gray-50 rounded-lg border border-gray-200 p-4 h-64 overflow-y-auto font-mono text-sm">
            <div class="text-gray-500 text-center py-8">
              No decisions yet. Start a job to see AI reasoning.
            </div>
          </div>
        </div>
      `
  
      this.attachEventListeners()
    }
  
    private attachEventListeners(): void {
      document.getElementById('clear-decisions')?.addEventListener('click', () => this.clearDecisions())
    }
  
    public addDecision(decision: any): void {
      const container = document.getElementById('decisions-container')
      if (!container) return
  
      // Remove empty state if present
      if (container.children.length === 1 && container.children[0].classList.contains('text-gray-500')) {
        container.innerHTML = ''
      }
  
      const entry = document.createElement('div')
      entry.className = 'mb-3 p-3 bg-white rounded border-l-4 border-blue-400'
      
      const timestamp = new Date().toLocaleTimeString()
      entry.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <span class="font-semibold text-blue-600">${decision.action?.toUpperCase() || 'UNKNOWN'}</span>
          <span class="text-xs text-gray-500">${timestamp}</span>
        </div>
        <div class="text-gray-700 mb-2">${decision.reason || 'No reason provided'}</div>
        ${decision.index !== undefined ? `<div class="text-xs text-gray-500">Element Index: ${decision.index}</div>` : ''}
        ${decision.text ? `<div class="text-xs text-gray-500">Text: "${decision.text}"</div>` : ''}
      `
      
      container.appendChild(entry)
      container.scrollTop = container.scrollHeight
  
      console.log('✅ Decision added to UI:', decision)
    }
  
    public clearDecisions(): void {
      const container = document.getElementById('decisions-container')
      if (!container) return
  
      container.innerHTML = `
        <div class="text-gray-500 text-center py-8">
          No decisions yet. Start a job to see AI reasoning.
        </div>
      `
    }
  }
  