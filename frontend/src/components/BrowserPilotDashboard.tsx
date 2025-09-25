import React, { useState, useEffect } from 'react';
import { Header } from './Header';
import { JobForm } from './JobForm';
import { StatusDisplay } from './StatusDisplay';
import { TokenUsage } from './TokenUsage';
import { DecisionLog } from './DecisionLog';
import { ScreenshotGallery } from './ScreenshotGallery';
import { StreamingViewer } from './StreamingViewer';
import { ProxyStats } from './ProxyStats';
import { WebSocketManager } from '../services/WebSocketManager';

export const BrowserPilotDashboard: React.FC = () => {
  const [wsManager] = useState(() => new WebSocketManager());
  const [status, setStatus] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);
  const [tokenUsage, setTokenUsage] = useState({
    prompt_tokens: 0,
    response_tokens: 0,
    total_tokens: 0,
    api_calls: 0
  });
  const [proxyStats, setProxyStats] = useState({
    available: 0,
    healthy: 0,
    blocked: 0,
    retry_count: 0
  });
  const [decisions, setDecisions] = useState<any[]>([]);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingEnabled, setStreamingEnabled] = useState(false);

  useEffect(() => {
    // Set up WebSocket event listeners
    wsManager.on('connected', () => {
      setStatus({ message: 'Connected to BrowserPilot server', type: 'success' });
      setIsLoading(false);
    });

    wsManager.on('decision', (data: any) => {
      const decision = data.decision || data;
      setDecisions(prev => [...prev, decision]);
      
      if (decision.token_usage) {
        updateTokenUsage(decision.token_usage);
      }
    });

    wsManager.on('screenshot', (data: any) => {
      const screenshot = data.screenshot || data;
      if (typeof screenshot === 'string') {
        setScreenshots(prev => [...prev, screenshot]);
      }
    });

    wsManager.on('proxy_stats', (data: any) => {
      setProxyStats(data.stats || data);
    });

    wsManager.on('token_usage', (data: any) => {
      updateTokenUsage(data.token_usage || data);
    });

    wsManager.on('page_info', (data: any) => {
      setStatus({
        message: `Navigating: ${data.url} • Found ${data.interactive_elements} interactive elements`,
        type: 'info'
      });
    });

    wsManager.on('extraction', (data: any) => {
      if (data.status === 'completed') {
        setStatus({
          message: `Extraction completed successfully in ${data.format?.toUpperCase()} format`,
          type: 'success'
        });
      }
    });

    wsManager.on('error', (data: any) => {
      setStatus({
        message: data.message || data.error || 'An unexpected error occurred',
        type: 'error'
      });
      setIsLoading(false);
    });

    return () => {
      wsManager.disconnect();
      wsManager.disconnectStream();
    };
  }, [wsManager]);

  const updateTokenUsage = (usage: any) => {
    setTokenUsage(prev => ({
      prompt_tokens: prev.prompt_tokens + (usage.prompt_tokens || 0),
      response_tokens: prev.response_tokens + (usage.response_tokens || 0),
      total_tokens: prev.total_tokens + (usage.total_tokens || 0),
      api_calls: prev.api_calls + 1
    }));
  };

  const handleJobCreated = (jobData: { jobId: string; streaming: boolean; format: string }) => {
    setCurrentJobId(jobData.jobId);
    setIsLoading(true);
    setStreamingEnabled(jobData.streaming);
    wsManager.connect(jobData.jobId);

    if (jobData.streaming) {
      wsManager.connectStream(jobData.jobId);
    } else {
      wsManager.disconnectStream();
    }
  };

  const clearDecisions = () => setDecisions([]);
  const clearScreenshots = () => setScreenshots([]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 via-amber-50/30 to-orange-50/20 dark:from-stone-900 dark:via-stone-800 dark:to-stone-700 transition-all duration-1000">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Welcome Animation */}
        <div className="text-center mb-12 animate-in fade-in slide-in-from-top-1 duration-1000">
          <h1 className="text-4xl font-light text-stone-800 dark:text-stone-200 mb-4 tracking-wide">
            Welcome to <span className="font-medium text-stone-700 dark:text-stone-300">BrowserPilot</span>
          </h1>
          <p className="text-stone-600 dark:text-stone-400 text-lg font-light max-w-2xl mx-auto leading-relaxed">
            Open-source alternative to Perplexity Comet and director.ai. Describe what you need, and watch as your browser comes to life.
          </p>
        </div>

        {/* Control Panel */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
          <div className="xl:col-span-2">
            <JobForm wsManager={wsManager} onJobCreated={handleJobCreated} />
          </div>
          
          <div className="space-y-6">
            <TokenUsage usage={tokenUsage} />
            <ProxyStats stats={proxyStats} />
          </div>
        </div>

        {/* Status Display */}
        {status && (
          <div className="animate-in fade-in slide-in-from-top-2 duration-500">
            <StatusDisplay status={status} onDismiss={() => setStatus(null)} />
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-center space-x-4">
              <div className="w-8 h-8 border-4 border-amber-200 border-t-amber-600 rounded-full animate-spin"></div>
              <p className="text-stone-700 font-medium">BrowserPilot is working...</p>
            </div>
          </div>
        )}

        {/* Browser Streaming */}
        <div className="animate-in fade-in slide-in-from-left-4 duration-700 delay-400">
          <StreamingViewer
            wsManager={wsManager}
            jobId={currentJobId}
            autoConnect={streamingEnabled}
          />
        </div>

        {/* Decision Log */}
        <div className="animate-in fade-in slide-in-from-right-4 duration-700 delay-500">
          <DecisionLog decisions={decisions} onClear={clearDecisions} />
        </div>

        {/* Screenshot Gallery */}
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-600">
          <ScreenshotGallery screenshots={screenshots} onClear={clearScreenshots} />
        </div>
      </main>

      {/* Floating Action Button */}
      <div className="fixed bottom-8 right-8 z-50">
        <button className="w-14 h-14 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-110 transition-all duration-300 flex items-center justify-center group">
          <div className="w-6 h-6 border-2 border-white rounded-sm group-hover:rotate-12 transition-transform duration-300"></div>
        </button>
      </div>
    </div>
  );
};
