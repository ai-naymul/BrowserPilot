import React, { useState, useEffect } from 'react';
import { Monitor, Play, Square, Camera, Settings, Circle, Maximize2 } from 'lucide-react';
import { WebSocketManager } from '../services/WebSocketManager';

interface StreamingViewerProps {
  wsManager: WebSocketManager;
  jobId: string | null;
}

export const StreamingViewer: React.FC<StreamingViewerProps> = ({ wsManager, jobId }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [streamStats, setStreamStats] = useState({ frameCount: 0, fps: 0 });
  const [showStream, setShowStream] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    wsManager.on('stream_connected', () => {
      setIsConnected(true);
    });

    wsManager.on('stream_disconnected', () => {
      setIsConnected(false);
    });

    wsManager.on('stream_frame', (data: any) => {
      setCurrentFrame(data.data);
      setStreamStats(prev => ({
        frameCount: prev.frameCount + 1,
        fps: prev.fps
      }));
    });

    wsManager.on('streaming_info', (data: any) => {
      if (data.streaming?.enabled) {
        setShowStream(true);
      }
    });
  }, [wsManager]);

  const handleConnect = () => {
    if (jobId) {
      wsManager.connectStream(jobId);
    }
  };

  const handleDisconnect = () => {
    wsManager.disconnectStream();
  };

  const handleStreamClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!isConnected) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (1280 / rect.width));
    const y = Math.round((e.clientY - rect.top) * (800 / rect.height));

    wsManager.sendStreamMessage({
      type: 'mouse',
      eventType: 'mousePressed',
      x,
      y,
      button: 'left',
      clickCount: 1
    });

    setTimeout(() => {
      wsManager.sendStreamMessage({
        type: 'mouse',
        eventType: 'mouseReleased',
        x,
        y,
        button: 'left'
      });
    }, 100);
  };

  if (!showStream) {
    return (
      <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 overflow-hidden transition-all duration-300 hover:shadow-md hover:bg-white/80">
        <div className="p-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-500 rounded-xl flex items-center justify-center shadow-md">
              <Monitor className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-medium text-stone-800">Live Browser View</h2>
              <p className="text-sm text-stone-600 font-light">Real-time browser streaming with interaction</p>
            </div>
          </div>

          <div className="bg-stone-50/80 dark:bg-stone-800/50 backdrop-blur-sm rounded-xl border-2 border-dashed border-stone-300/60 dark:border-stone-600/60 p-16 text-center">
            <div className="w-20 h-20 bg-stone-200/80 dark:bg-stone-700/80 rounded-2xl mx-auto mb-6 flex items-center justify-center">
              <Monitor className="w-10 h-10 text-stone-400 dark:text-stone-500" />
            </div>
            <h3 className="text-xl font-medium text-stone-800 dark:text-stone-200 mb-3">Browser Streaming</h3>
            <p className="text-stone-600 dark:text-stone-400 font-light mb-6 max-w-md mx-auto leading-relaxed">
              Enable streaming to watch BrowserPilot navigate websites in real-time
            </p>
            <button
              onClick={() => setShowStream(true)}
              className="px-6 py-3 bg-gradient-to-r from-stone-500 to-stone-600 text-white rounded-xl hover:from-stone-600 hover:to-stone-700 transition-all duration-300 flex items-center space-x-3 mx-auto group shadow-md hover:shadow-lg"
            >
              <Play className="w-5 h-5 group-hover:scale-110 transition-transform duration-300" />
              <span className="font-medium">Enable Live Streaming</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 overflow-hidden transition-all duration-300 hover:shadow-md hover:bg-white/80">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-stone-400 to-stone-500 dark:from-stone-500 dark:to-stone-600 rounded-xl flex items-center justify-center shadow-md">
              <Monitor className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-medium text-stone-800 dark:text-stone-200">Live Browser View</h2>
              <p className="text-sm text-stone-600 dark:text-stone-400 font-light">Real-time browser streaming with interaction</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-all duration-300 ${
              isConnected 
                ? 'bg-sage-100/80 dark:bg-sage-800/50 text-sage-800 dark:text-sage-200 backdrop-blur-sm' 
                : 'bg-blush-100/80 dark:bg-blush-800/50 text-blush-800 dark:text-blush-200 backdrop-blur-sm'
            }`}>
              <Circle className={`w-2 h-2 ${isConnected ? 'text-sage-600 dark:text-sage-400 fill-current animate-pulse' : 'text-blush-600 dark:text-blush-400 fill-current'}`} />
              <span>{isConnected ? 'Live' : 'Offline'}</span>
            </div>
            <span className="text-xs text-stone-500 dark:text-stone-400 font-light">{streamStats.fps} FPS</span>
          </div>
        </div>

        <div className="relative bg-stone-900 dark:bg-stone-950 rounded-xl overflow-hidden border border-stone-200/60 dark:border-stone-600/60 shadow-lg">
          {currentFrame ? (
            <img
              src={`data:image/jpeg;base64,${currentFrame}`}
              alt="Browser Stream"
              className="w-full h-auto cursor-pointer hover:opacity-95 transition-opacity duration-200"
              onClick={handleStreamClick}
            />
          ) : (
            <div className="aspect-video flex items-center justify-center bg-stone-900 dark:bg-stone-950">
              <div className="text-center animate-in fade-in duration-500">
                <Monitor className="w-16 h-16 text-stone-400 dark:text-stone-500 mx-auto mb-4" />
                <p className="text-stone-300 dark:text-stone-400 text-sm font-light">Waiting for stream data...</p>
              </div>
            </div>
          )}

          {/* Stream Controls Overlay */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-black/70 backdrop-blur-md rounded-xl p-4 border border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleConnect}
                    disabled={isConnected || !jobId}
                    className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2 group"
                  >
                    <Play className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
                    <span>Connect</span>
                  </button>
                  <button
                    onClick={handleDisconnect}
                    disabled={!isConnected}
                    className="px-4 py-2 bg-rose-500 text-white rounded-lg text-sm hover:bg-rose-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2 group"
                  >
                    <Square className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
                    <span>Disconnect</span>
                  </button>
                  <button className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-all duration-200 flex items-center space-x-2 group">
                    <Camera className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
                    <span>Capture</span>
                  </button>
                </div>

                <div className="flex items-center space-x-3 text-white text-sm">
                  <button className="p-2 hover:bg-white/10 rounded-lg transition-colors duration-200">
                    <Maximize2 className="w-4 h-4" />
                  </button>
                  <Settings className="w-4 h-4" />
                  <select className="bg-stone-700/80 text-white rounded-lg px-3 py-1 text-xs border-0 focus:ring-2 focus:ring-purple-500 backdrop-blur-sm">
                    <option value="60">Low Quality</option>
                    <option value="80" selected>Medium Quality</option>
                    <option value="100">High Quality</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};