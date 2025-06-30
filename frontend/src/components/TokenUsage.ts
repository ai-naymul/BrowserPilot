export class TokenUsage {
    private totalTokenUsage = { 
      prompt_tokens: 0, 
      response_tokens: 0, 
      total_tokens: 0, 
      api_calls: 0 
    }
  
    public render(selector: string): void {
      const container = document.querySelector(selector)
      if (!container) return
  
      container.innerHTML = `
        <div class="p-6">
          <div class="flex items-center space-x-3 mb-6">
            <div class="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold">📊</span>
            </div>
            <div>
              <h2 class="text-lg font-semibold text-gray-900">Token Usage</h2>
              <p class="text-sm text-gray-500">AI model consumption tracking</p>
            </div>
          </div>
  
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
              <div class="text-2xl font-bold text-blue-600" id="total-tokens">0</div>
              <div class="text-sm text-blue-700 font-medium">Total Tokens</div>
            </div>
            
            <div class="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
              <div class="text-2xl font-bold text-green-600" id="prompt-tokens">0</div>
              <div class="text-sm text-green-700 font-medium">Prompt Tokens</div>
            </div>
            
            <div class="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
              <div class="text-2xl font-bold text-purple-600" id="response-tokens">0</div>
              <div class="text-sm text-purple-700 font-medium">Response Tokens</div>
            </div>
            
            <div class="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
              <div class="text-2xl font-bold text-orange-600" id="api-calls">0</div>
              <div class="text-sm text-orange-700 font-medium">API Calls</div>
            </div>
          </div>
        </div>
      `
    }
  
    public updateUsage(usage: any): void {
      this.totalTokenUsage.prompt_tokens += usage.prompt_tokens || 0
      this.totalTokenUsage.response_tokens += usage.response_tokens || 0
      this.totalTokenUsage.total_tokens += usage.total_tokens || 0
      this.totalTokenUsage.api_calls += 1
  
      this.updateDisplay()
    }
  
    private updateDisplay(): void {
      const totalElement = document.getElementById('total-tokens')
      const promptElement = document.getElementById('prompt-tokens')
      const responseElement = document.getElementById('response-tokens')
      const callsElement = document.getElementById('api-calls')
  
      if (totalElement) totalElement.textContent = this.totalTokenUsage.total_tokens.toString()
      if (promptElement) promptElement.textContent = this.totalTokenUsage.prompt_tokens.toString()
      if (responseElement) responseElement.textContent = this.totalTokenUsage.response_tokens.toString()
      if (callsElement) callsElement.textContent = this.totalTokenUsage.api_calls.toString()
    }
  
    public reset(): void {
      this.totalTokenUsage = { prompt_tokens: 0, response_tokens: 0, total_tokens: 0, api_calls: 0 }
      this.updateDisplay()
    }
  }
  