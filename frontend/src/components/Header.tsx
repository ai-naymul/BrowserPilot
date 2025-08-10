import React, { useState } from 'react';
import { Activity, Settings, User, Moon, Sun } from 'lucide-react';

export const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="bg-white/80 dark:bg-stone-900/80 backdrop-blur-md shadow-sm border-b border-stone-200/60 dark:border-stone-700/60 sticky top-0 z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4 group">
            {/* Logo Placeholder - You can replace this with your SVG */}
            <div className="w-10 h-10 bg-gradient-to-br from-stone-600 to-stone-700 dark:from-stone-300 dark:to-stone-400 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-300 group-hover:scale-105">
              <div className="w-6 h-6 border-2 border-white dark:border-stone-800 rounded-sm transform group-hover:rotate-12 transition-transform duration-300"></div>
            </div>
            <div className="transform group-hover:translate-x-1 transition-transform duration-300">
              <h1 className="text-xl font-medium text-stone-800 dark:text-stone-200 tracking-wide">BrowserPilot</h1>
              <p className="text-xs text-stone-500 dark:text-stone-400 -mt-1 font-light">Open-source alternative to Perplexity Comet</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            {/* Status Indicator */}
            <div className="flex items-center space-x-3 px-4 py-2 bg-stone-50 dark:bg-stone-800 rounded-full border border-stone-200/60 dark:border-stone-700/60 hover:bg-stone-100 dark:hover:bg-stone-700 transition-colors duration-200">
              <Activity className="w-4 h-4 text-emerald-500 animate-pulse" />
              <span className="text-sm text-stone-600 dark:text-stone-300 font-medium">Active</span>
            </div>

            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="w-10 h-10 bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-105"
            >
              {isDarkMode ? (
                <Sun className="w-5 h-5 text-stone-600 dark:text-stone-300" />
              ) : (
                <Moon className="w-5 h-5 text-stone-600 dark:text-stone-300" />
              )}
            </button>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="w-10 h-10 bg-stone-100 dark:bg-stone-800 hover:bg-stone-200 dark:hover:bg-stone-700 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-105"
              >
                <User className="w-5 h-5 text-stone-600 dark:text-stone-300" />
              </button>

              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-stone-800 rounded-xl shadow-lg border border-stone-200/60 dark:border-stone-700/60 py-2 animate-in fade-in slide-in-from-top-2 duration-200">
                  <button className="w-full px-4 py-2 text-left text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-700 transition-colors duration-150 flex items-center space-x-3">
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </button>
                  <a 
                    href="https://browserpilot-alpha.vercel.app/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="w-full px-4 py-2 text-left text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-700 transition-colors duration-150 flex items-center space-x-3"
                  >
                    <Activity className="w-4 h-4" />
                    <span>Visit Landing Page</span>
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};