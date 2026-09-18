import React from 'react';
import { BookOpen, BookMarked, Music, Sparkles } from 'lucide-react';

export default function MobileBottomNav({ currentView, setView }) {
  const navItems = [
    { id: 'home', label: 'Home', icon: Sparkles },
    { id: 'lessons', label: 'Lessons', icon: BookOpen },
    { id: 'stories', label: 'Stories', icon: BookMarked },
    { id: 'songs', label: 'Lyrics', icon: Music },
  ];

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#0b0f19]/95 backdrop-blur-md border-t border-[#243049]"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      <div className="flex items-stretch justify-around">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              className={`relative flex flex-col items-center justify-center gap-1 py-3 px-2 flex-1 text-xs transition-colors ${
                isActive
                  ? 'text-amber-400 font-semibold'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Icon
                size={20}
                className={isActive ? 'text-amber-400' : 'text-slate-500'}
              />
              <span className="text-[10px] leading-none">{item.label}</span>
              {isActive && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-0.5 rounded-full bg-amber-400" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
