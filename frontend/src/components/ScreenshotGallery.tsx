import React, { useState } from 'react'
import { Camera, X, Maximize2 } from 'lucide-react'

interface ScreenshotGalleryProps {
  screenshots: string[]
  onClear: () => void
}

export const ScreenshotGallery: React.FC<ScreenshotGalleryProps> = ({ screenshots, onClear }) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)

  const handleImageClick = (screenshot: string) => {
    setSelectedImage(screenshot)
  }

  const closeModal = () => {
    setSelectedImage(null)
  }

  return (
    <div className="animate-fade-in-up" style={{ animationDelay: '0.6s' }}>
      <div className="bg-white/80 dark:bg-stone-800/80 backdrop-blur-sm rounded-2xl border border-stone-200/50 dark:border-stone-700/50 shadow-lg hover:shadow-xl transition-all duration-300">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-stone-400 to-stone-500 rounded-xl flex items-center justify-center shadow-sm">
                <Camera className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-stone-900 dark:text-stone-100">Screenshots</h2>
                <p className="text-sm text-stone-600 dark:text-stone-400">Captured browser states during automation</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className="text-sm text-stone-500 dark:text-stone-400">
                {screenshots.length} screenshot{screenshots.length !== 1 ? 's' : ''}
              </span>
              <button 
                onClick={onClear}
                className="px-3 py-1.5 text-xs bg-stone-100 dark:bg-stone-700 text-stone-600 dark:text-stone-300 rounded-lg hover:bg-stone-200 dark:hover:bg-stone-600 transition-colors duration-200"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
            {screenshots.length === 0 ? (
              <div className="col-span-full text-stone-500 dark:text-stone-400 text-center py-12">
                <Camera className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No screenshots captured yet</p>
                <p className="text-sm mt-1">Screenshots will appear here as the agent runs</p>
              </div>
            ) : (
              screenshots.map((screenshot, index) => (
                <div 
                  key={index}
                  className="relative group cursor-pointer transform hover:scale-105 transition-all duration-300"
                  onClick={() => handleImageClick(screenshot)}
                >
                  <img 
                    src={`data:image/png;base64,${screenshot}`}
                    className="w-full h-32 object-cover rounded-xl border border-stone-200 dark:border-stone-700 shadow-sm group-hover:shadow-md transition-all duration-300" 
                    alt={`Screenshot ${index + 1}`}
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-300 rounded-xl flex items-center justify-center">
                    <Maximize2 className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  </div>
                  <div className="absolute bottom-2 left-2 right-2">
                    <div className="bg-black/70 text-white text-xs px-2 py-1 rounded-lg backdrop-blur-sm">
                      Screenshot {index + 1} - {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Modal for full-size image */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
          onClick={closeModal}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={closeModal}
              className="absolute -top-12 right-0 text-white hover:text-stone-300 transition-colors"
            >
              <X className="w-8 h-8" />
            </button>
            <img
              src={`data:image/png;base64,${selectedImage}`}
              className="max-w-full max-h-full object-contain rounded-xl shadow-2xl"
              alt="Full size screenshot"
            />
          </div>
        </div>
      )}
    </div>
  )
}