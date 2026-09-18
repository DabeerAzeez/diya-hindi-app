import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MobileBottomNav from './components/MobileBottomNav';
import ProfileDrawer from './components/ProfileDrawer';
import HomeView from './views/HomeView';
import LessonsView from './views/LessonsView';
import StoriesView from './views/StoriesView';
import SongsView from './views/SongsView';

import { getStatus, pingHeartbeat } from './services/api';

export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [profileOpen, setProfileOpen] = useState(false);
  const [ankiStatus, setAnkiStatus] = useState({ connected: false });

  // Heartbeat & status ping
  useEffect(() => {
    const pingStatus = () => {
      pingHeartbeat();
      getStatus()
        .then((data) => {
          setAnkiStatus({ connected: data.anki_connected, mode: data.mode });
        })
        .catch(() => {
          setAnkiStatus({ connected: false });
        });
    };

    pingStatus();
    const interval = setInterval(pingStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950">
      
      {/* Navigation Header */}
      <Navbar
        currentView={currentView}
        setView={setCurrentView}
        ankiStatus={ankiStatus}
        onOpenProfile={() => setProfileOpen(true)}
      />

      {/* Main View Display — pb-20 on mobile to clear the fixed bottom nav */}
      <main className="flex-1 pb-20 md:pb-16">
        {currentView === 'home' && <HomeView setView={setCurrentView} />}
        {currentView === 'lessons' && <LessonsView />}
        {currentView === 'stories' && <StoriesView />}
        {currentView === 'songs' && <SongsView />}
      </main>

      {/* Profile & Settings Drawer */}
      <ProfileDrawer
        isOpen={profileOpen}
        onClose={() => setProfileOpen(false)}
      />

      {/* Mobile Fixed Bottom Navigation */}
      <MobileBottomNav currentView={currentView} setView={setCurrentView} />

      {/* Footer — hidden on mobile so it doesn't crowd the bottom nav */}
      <footer className="hidden md:block border-t border-[#243049]/60 py-6 text-center text-xs text-slate-500">
        <p>🪔 DIYA • Personal Hindi Language Learning Hub</p>
      </footer>
    </div>
  );
}

