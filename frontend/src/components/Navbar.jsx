import React from 'react';
import { BookOpen, BookMarked, Music, Sparkles } from 'lucide-react';

export default function Navbar({ currentView, setView, ankiStatus, onOpenProfile }) {
  const navItems = [
    { id: 'home', label: 'Home', icon: Sparkles },
    { id: 'lessons', label: 'Lessons', icon: BookOpen },
    { id: 'stories', label: 'Stories', icon: BookMarked },
    { id: 'songs', label: 'Song Lyrics', icon: Music },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#243049] bg-[#0b0f19]/90 backdrop-blur-md px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        
        {/* Brand Logo */}
        <div 
          onClick={() => setView('home')} 
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 flex items-center justify-center text-2xl shadow-sm group-hover:border-amber-400/50 transition-all">
            🪔
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-white text-lg group-hover:text-amber-400 transition-colors">
                DIYA
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                Hub
              </span>
            </div>
            <p className="text-xs text-slate-400">Hindi Language Mentor</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="hidden md:flex items-center gap-1.5 bg-[#151d2f] p-1 rounded-xl border border-[#243049]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setView(item.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-300 hover:text-white hover:bg-[#1c263d]'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-white' : 'text-slate-400'} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Right Controls: Anki Indicator & Profile */}
        <div className="flex items-center gap-3">
          
          {/* Anki Live Connection Status Indicator */}
          <div 
            title={
              ankiStatus?.connected 
                ? 'Anki Live (:8765)' 
                : ankiStatus?.mode === 'cloud'
                ? 'Anki Cloud Mode (Reading local deck snapshot)'
                : 'Anki Offline — Run Anki with AnkiConnect locally'
            }
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#151d2f] border border-[#243049] text-xs select-none shadow-sm"
          >
            <span className={`w-2 h-2 rounded-full ${
              ankiStatus?.connected 
                ? 'bg-emerald-400 pulse-dot shadow-sm shadow-emerald-500/50' 
                : ankiStatus?.mode === 'cloud'
                ? 'bg-cyan-400'
                : 'bg-rose-500'
            }`} />
            <span className="text-slate-300 font-medium">
              {ankiStatus?.connected 
                ? 'Anki Live' 
                : ankiStatus?.mode === 'cloud'
                ? 'Cloud (Snapshot)'
                : 'Anki Offline'}
            </span>
          </div>

          {/* Profile Trigger */}
          <button
            onClick={onOpenProfile}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#151d2f] hover:bg-[#1c263d] border border-[#243049] text-sm text-slate-200 hover:text-white transition-all shadow-sm group"
          >
            <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold">
              👤
            </div>
            <span className="font-medium hidden sm:inline">Profile</span>
          </button>

        </div>
      </div>

    </header>
  );
}
