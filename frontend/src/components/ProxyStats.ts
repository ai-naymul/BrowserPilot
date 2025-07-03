export class ProxyStats {
    public render(selector: string) {
      const container = document.querySelector(selector)
      if (!container) return
  
      container.innerHTML = `
        <div class="p-6">
          <div class="flex items-center space-x-3 mb-6">
            <div class="w-10 h-10 bg-gradient-to-r from-orange-400 to-red-500 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold">🔄</span>
            </div>
            <div>
              <h2 class="text-lg font-semibold text-gray-900">Proxy Status</h2>
              <p class="text-sm text-gray-500">Smart rotation and health tracking</p>
            </div>
          </div>
  
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
              <div class="text-2xl font-bold text-green-600" id="available-proxies">0</div>
              <div class="text-sm text-green-700 font-medium">Available</div>
            </div>
            
            <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
              <div class="text-2xl font-bold text-blue-600" id="healthy-proxies">0</div>
              <div class="text-sm text-blue-700 font-medium">Healthy</div>
            </div>
            
            <div class="bg-gradient-to-r from-yellow-50 to-yellow-100 p-4 rounded-lg border border-yellow-200">
              <div class="text-2xl font-bold text-yellow-600" id="blocked-proxies">0</div>
              <div class="text-sm text-yellow-700 font-medium">Blocked</div>
            </div>
            
            <div class="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
              <div class="text-2xl font-bold text-red-600" id="retry-count">0</div>
              <div class="text-sm text-red-700 font-medium">Retries</div>
            </div>
          </div>
        </div>
      `
    }
  
    public updateStats(stats: any) {
      const availableElement = document.getElementById('available-proxies')
      const healthyElement = document.getElementById('healthy-proxies')
      const blockedElement = document.getElementById('blocked-proxies')
      const retryElement = document.getElementById('retry-count')
  
      if (availableElement) availableElement.textContent = (stats.available || 0).toString()
      if (healthyElement) healthyElement.textContent = (stats.healthy || 0).toString()
      if (blockedElement) blockedElement.textContent = (stats.blocked || 0).toString()
      if (retryElement) retryElement.textContent = (stats.retry_count || 0).toString()
    }
  }
  