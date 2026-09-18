import React from 'react';
import { BookOpen, BookMarked, Music, ArrowRight, Sparkles } from 'lucide-react';

export default function HomeView({ setView }) {
  const modules = [
    {
      id: 'lessons',
      title: 'Lessons',
      tag: 'Core Grammar & Quizzes',
      tagColor: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      description: 'Explore sequential Hindi lessons with clear explanations, LaTeX formulas, dialogue examples, and interactive practice quizzes.',
      icon: BookOpen,
      iconBg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
      hoverBorder: 'hover:border-amber-500/50',
      countLabel: '35 Curriculum Modules',
    },
    {
      id: 'stories',
      title: 'Stories',
      tag: 'Bilingual E-Reader',
      tagColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
      description: 'Read immersive bilingual stories set in Norwich with synchronized sentence highlighting, word-by-word hover glosses, and audio playback.',
      icon: BookMarked,
      iconBg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400',
      hoverBorder: 'hover:border-cyan-500/50',
      countLabel: 'Interactive Stories',
    },
    {
      id: 'songs',
      title: 'Song Lyrics',
      tag: '4-Layer Linguistic Breakdowns',
      tagColor: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
      description: 'Deconstruct Hindi & Bollywood songs line-by-line with word-by-word breakdowns, literal translations, and idiomatic English meanings.',
      icon: Music,
      iconBg: 'bg-purple-500/15 border-purple-500/30 text-purple-400',
      hoverBorder: 'hover:border-purple-500/50',
      countLabel: '4 Bollywood Breakdowns',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 animate-fade-in">
      
      {/* Welcome Banner */}
      <div className="text-center max-w-2xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#151d2f] border border-[#243049] text-xs text-amber-400 font-medium mb-5 shadow-sm">
          <Sparkles size={14} className="text-amber-400" />
          <span>Namaste & Welcome</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-tight mb-4">
          Your Personal Hindi Learning Hub
        </h1>
        <p className="text-base sm:text-lg text-slate-400 leading-relaxed">
          Choose a section below to continue your journey toward conversational fluency.
        </p>
      </div>

      {/* 3 Main Module Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
        {modules.map((mod) => {
          const Icon = mod.icon;
          return (
            <div
              key={mod.id}
              onClick={() => setView(mod.id)}
              className={`group relative rounded-2xl bg-[#151d2f] border border-[#243049] p-7 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-2xl hover:shadow-black/40 cursor-pointer flex flex-col justify-between ${mod.hoverBorder}`}
            >
              <div>
                {/* Header with Icon & Tag */}
                <div className="flex items-start justify-between gap-4 mb-6">
                  <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center text-2xl transition-transform group-hover:scale-105 ${mod.iconBg}`}>
                    <Icon size={28} />
                  </div>
                  <span className={`text-[11px] font-semibold tracking-wide uppercase px-2.5 py-1 rounded-full border ${mod.tagColor}`}>
                    {mod.tag}
                  </span>
                </div>

                {/* Title & Description */}
                <h3 className="text-xl font-bold text-white mb-2.5 group-hover:text-amber-400 transition-colors">
                  {mod.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-6">
                  {mod.description}
                </p>
              </div>

              {/* Card Footer */}
              <div className="pt-4 border-t border-[#243049]/60 flex items-center justify-between text-xs">
                <span className="font-medium text-slate-400">
                  {mod.countLabel}
                </span>
                <span className="inline-flex items-center gap-1 font-semibold text-amber-400 group-hover:translate-x-1 transition-transform">
                  Explore <ArrowRight size={14} />
                </span>
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
