import React, { useState, useEffect } from 'react';
import { Play, Download, Monitor, Eye, EyeOff, Sparkles, ArrowRight } from 'lucide-react';
import { WebSocketManager } from '../services/WebSocketManager';

interface JobFormProps {
  wsManager: WebSocketManager;
  onJobCreated: (data: { jobId: string; streaming: boolean; format: string }) => void;
}

export const JobForm: React.FC<JobFormProps> = ({ wsManager, onJobCreated }) => {
  const [prompt, setPrompt] = useState('Navigate to Hacker News and extract the top 10 stories as JSON with titles, URLs, and scores');
  const [format, setFormat] = useState('json');
  const [headless, setHeadless] = useState(false);
  const [streaming, setStreaming] = useState(true);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [detectedFormat, setDetectedFormat] = useState<string | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    const detected = detectFormatFromPrompt(prompt);
    setDetectedFormat(detected);
  }, [prompt]);

  const detectFormatFromPrompt = (text: string): string | null => {
    const lower = text.toLowerCase();
    const patterns = {
      pdf: [/\bpdf\b/, /pdf format/, /save.*pdf/, /as pdf/, /to pdf/],
      csv: [/\bcsv\b/, /csv format/, /save.*csv/, /as csv/, /to csv/],
      json: [/\bjson\b/, /json format/, /save.*json/, /as json/, /to json/],
      html: [/\bhtml\b/, /html format/, /save.*html/, /as html/, /to html/],
      md: [/\bmarkdown\b/, /md format/, /save.*markdown/, /as markdown/, /to md/],
      txt: [/\btext\b/, /txt format/, /save.*text/, /as text/, /to txt/, /plain text/]
    };

    for (const [fmt, regexes] of Object.entries(patterns)) {
      if (regexes.some(regex => regex.test(lower))) {
        return fmt;
      }
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isSubmitting) return;

    setIsSubmitting(true);
    const finalFormat = detectedFormat || format;

    try {
      const response = await fetch('/job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          format: finalFormat,
          headless,
          enable_streaming: streaming
        })
      });

      const data = await response.json();
      setCurrentJobId(data.job_id);
      onJobCreated({
        jobId: data.job_id,
        streaming,
        format: finalFormat
      });
    } catch (error) {
      console.error('Error creating job:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownload = async () => {
    if (!currentJobId) return;

    try {
      const response = await fetch(`/download/${currentJobId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `browserpilot_result_${currentJobId}.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download error:', error);
    }
  };

  return (
    <div 
      className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-stone-200/60 overflow-hidden transition-all duration-500 hover:shadow-md hover:bg-white/80"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="p-8">
        <div className="flex items-center space-x-4 mb-8">
          <div className={`w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-md transition-all duration-300 ${isHovered ? 'scale-110 rotate-3' : ''}`}>
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-medium text-stone-800 mb-1">Create Automation Task</h2>
            <p className="text-stone-600 font-light">Describe what you want to accomplish, and BrowserPilot will handle the rest</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Task Description */}
          <div className="space-y-3">
            <label htmlFor="prompt" className="block text-sm font-medium text-stone-700">
              Task Description
              <span className="text-stone-500 font-light ml-2">(natural language works best)</span>
            </label>
            <div className="relative">
              <textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                className="w-full px-4 py-4 border border-stone-300/60 dark:border-stone-600/60 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all duration-200 resize-none text-stone-800 dark:text-stone-200 placeholder-stone-400 dark:placeholder-stone-500 bg-white/50 dark:bg-stone-800/50 backdrop-blur-sm"
                placeholder="Examples:&#10;• Navigate to Amazon and find wireless headphones under $100&#10;• Go to LinkedIn and extract AI engineer profiles in San Francisco&#10;• Visit news.ycombinator.com and save top stories as JSON"
              />
              <div className="absolute bottom-3 right-3">
                <ArrowRight className="w-5 h-5 text-stone-400" />
              </div>
            </div>
            
            {/* Example Prompts */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-3">
                Quick Examples
                <span className="text-stone-500 dark:text-stone-400 font-light ml-2">(click to use)</span>
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setPrompt("Go to https://news.ycombinator.com and save top stories as JSON")}
                  className="text-left p-3 bg-stone-50/80 dark:bg-stone-800/50 hover:bg-stone-100/80 dark:hover:bg-stone-700/50 border border-stone-200/60 dark:border-stone-600/60 rounded-lg transition-all duration-200 group backdrop-blur-sm"
                >
                  <div className="text-sm font-medium text-stone-700 dark:text-stone-300 group-hover:text-stone-900 dark:group-hover:text-stone-100">
                    Hacker News Stories
                  </div>
                  <div className="text-xs text-stone-500 dark:text-stone-400 mt-1">
                    Extract top stories as JSON
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => setPrompt("Visit firecrawl.dev pricing page and save to PDF format")}
                  className="text-left p-3 bg-stone-50/80 dark:bg-stone-800/50 hover:bg-stone-100/80 dark:hover:bg-stone-700/50 border border-stone-200/60 dark:border-stone-600/60 rounded-lg transition-all duration-200 group backdrop-blur-sm"
                >
                  <div className="text-sm font-medium text-stone-700 dark:text-stone-300 group-hover:text-stone-900 dark:group-hover:text-stone-100">
                    Save Page as PDF
                  </div>
                  <div className="text-xs text-stone-500 dark:text-stone-400 mt-1">
                    Convert webpage to PDF
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => setPrompt("Search 'AI tools' and export results as CSV")}
                  className="text-left p-3 bg-stone-50/80 dark:bg-stone-800/50 hover:bg-stone-100/80 dark:hover:bg-stone-700/50 border border-stone-200/60 dark:border-stone-600/60 rounded-lg transition-all duration-200 group backdrop-blur-sm"
                >
                  <div className="text-sm font-medium text-stone-700 dark:text-stone-300 group-hover:text-stone-900 dark:group-hover:text-stone-100">
                    Search & Export CSV
                  </div>
                  <div className="text-xs text-stone-500 dark:text-stone-400 mt-1">
                    Search results to spreadsheet
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => setPrompt("Find AI engineers in San Francisco on LinkedIn and save their profiles")}
                  className="text-left p-3 bg-stone-50/80 dark:bg-stone-800/50 hover:bg-stone-100/80 dark:hover:bg-stone-700/50 border border-stone-200/60 dark:border-stone-600/60 rounded-lg transition-all duration-200 group backdrop-blur-sm"
                >
                  <div className="text-sm font-medium text-stone-700 dark:text-stone-300 group-hover:text-stone-900 dark:group-hover:text-stone-100">
                    LinkedIn Profiles
                  </div>
                  <div className="text-xs text-stone-500 dark:text-stone-400 mt-1">
                    Extract professional profiles
                  </div>
                </button>
              </div>
            </div>
          </div>

          {/* Format Detection Indicator */}
          {detectedFormat && (
            <div className="p-4 bg-amber-50/80 backdrop-blur-sm border border-amber-200/60 rounded-xl animate-in fade-in slide-in-from-top-1 duration-300">
              <div className="flex items-center">
                <Sparkles className="w-4 h-4 text-amber-600 mr-3" />
                <span className="text-sm font-medium text-amber-800">Smart Detection:</span>
                <span className="ml-2 text-sm text-amber-700 font-mono uppercase bg-amber-100 px-2 py-1 rounded-md">
                  {detectedFormat} format detected
                </span>
              </div>
            </div>
          )}

          {/* Configuration Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Format Selection */}
            <div className="space-y-3">
              <label htmlFor="format" className="block text-sm font-medium text-stone-700">
                Output Format
              </label>
              <select
                id="format"
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full px-4 py-3 border border-stone-300/60 dark:border-stone-600/60 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all duration-200 text-stone-800 dark:text-stone-200 bg-white/50 dark:bg-stone-800/50 backdrop-blur-sm"
              >
                <option value="txt">Plain Text (TXT)</option>
                <option value="md">Markdown (MD)</option>
                <option value="json">JSON</option>
                <option value="html">HTML</option>
                <option value="csv">CSV</option>
                <option value="pdf">PDF</option>
              </select>
            </div>

            {/* Options */}
            <div className="space-y-4">
              <label className="block text-sm font-medium text-stone-700">Automation Options</label>
              <div className="space-y-4">
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={headless}
                    onChange={(e) => setHeadless(e.target.checked)}
                    className="w-4 h-4 text-amber-600 border-stone-300 dark:border-stone-600 rounded focus:ring-amber-500/20 focus:ring-2 bg-white dark:bg-stone-800"
                  />
                  <div className="ml-3 flex items-center">
                    {headless ? (
                      <EyeOff className="w-4 h-4 text-stone-600 dark:text-stone-400 mr-2" />
                    ) : (
                      <Eye className="w-4 h-4 text-stone-600 dark:text-stone-400 mr-2" />
                    )}
                    <span className="text-sm text-stone-700 dark:text-stone-300 group-hover:text-stone-900 dark:group-hover:text-stone-100 transition-colors">
                      Headless Mode
                    </span>
                  </div>
                </label>
                <label className="flex items-center cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={streaming}
                    onChange={(e) => setStreaming(e.target.checked)}
                    className="w-4 h-4 text-amber-600 border-stone-300 dark:border-stone-600 rounded focus:ring-amber-500/20 focus:ring-2 bg-white dark:bg-stone-800"
                  />
                  <div className="ml-3 flex items-center">
                    <Monitor className="w-4 h-4 text-stone-600 dark:text-stone-400 mr-2" />
                    <span className="text-sm text-stone-700 dark:text-stone-300 group-hover:text-stone-900 dark:group-hover:text-stone-100 transition-colors">
                      Live Streaming
                    </span>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 pt-6 border-t border-stone-200/60">
            <button
              type="submit"
              disabled={isSubmitting || !prompt.trim()}
              className="flex-1 min-w-0 bg-gradient-to-r from-amber-500 to-orange-500 text-white px-8 py-4 rounded-xl font-medium hover:from-amber-600 hover:to-orange-600 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center justify-center space-x-3 group shadow-md hover:shadow-lg"
            >
              <Play className={`w-5 h-5 transition-transform duration-300 ${isSubmitting ? 'animate-spin' : 'group-hover:scale-110'}`} />
              <span className="text-lg">{isSubmitting ? 'Launching BrowserPilot...' : 'Start Automation'}</span>
            </button>

            <button
              type="button"
              onClick={handleDownload}
              disabled={!currentJobId}
              className="px-8 py-4 border border-stone-300/60 dark:border-stone-600/60 text-stone-700 dark:text-stone-300 rounded-xl font-medium hover:bg-stone-50 dark:hover:bg-stone-700/50 hover:border-stone-400 dark:hover:border-stone-500 focus:outline-none focus:ring-2 focus:ring-stone-500/20 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center space-x-3 group bg-white/50 dark:bg-stone-800/50 backdrop-blur-sm"
            >
              <Download className="w-5 h-5 group-hover:scale-110 transition-transform duration-300" />
              <span>Download Results</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};