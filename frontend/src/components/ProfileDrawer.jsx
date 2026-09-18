import React, { useState, useEffect } from 'react';
import { X, Save, CheckCircle2, Sparkles, FileText, AlertCircle } from 'lucide-react';
import { getProfile, saveProfile } from '../services/api';
import RichTextEditor from './RichTextEditor';

export default function ProfileDrawer({ isOpen, onClose }) {
  const [profile, setProfile] = useState({
    name: '',
    pronouns: 'He/Him',
    gender: 'Male',
    diya_instructions: '',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setSaved(false);
      setError(null);
      getProfile()
        .then((data) => {
          setProfile({
            name: data.name || '',
            pronouns: data.pronouns || 'He/Him',
            gender: data.gender || 'Male',
            diya_instructions: data.diya_instructions || '',
            notes: data.notes || '',
          });
        })
        .catch(() => setError('Failed to load profile data'));
    }
  }, [isOpen]);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await saveProfile(profile);
      setLoading(false);
      if (res.success || res.status === 'saved_locally') {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      } else {
        setError(res.error || 'Failed to save');
      }
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Failed to save');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-lg bg-[#0f172a] border-l border-[#243049] shadow-2xl h-full flex flex-col z-10 animate-fade-in">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-[#243049] bg-[#151d2f]/70">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-lg">
              👤
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Learner Profile & Diya Settings</h2>
              <p className="text-xs text-slate-400">Synced across DIYA and your Antigravity coach</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-[#1c263d] transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-2">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {/* Name & Pronouns Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Your Name
              </label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                placeholder="e.g. Student"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#151d2f] border border-[#243049] text-white text-sm focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Grammar Gender & Pronouns
              </label>
              <select
                value={profile.gender}
                onChange={(e) => setProfile({ 
                  ...profile, 
                  gender: e.target.value,
                  pronouns: e.target.value === 'Male' ? 'He/Him' : 'She/Her'
                })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#151d2f] border border-[#243049] text-white text-sm focus:outline-none focus:border-amber-500 transition-colors"
              >
                <option value="Male">Male (-taa hoon / -aa)</option>
                <option value="Female">Female (-tii hoon / -ii)</option>
              </select>
            </div>
          </div>

          {/* System Instructions for Diya */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles size={14} className="text-amber-400" />
                System Instructions for Diya
              </label>
            </div>
            <p className="text-xs text-slate-400 mb-2">
              Guidance for how Diya should teach, reinforce rules, or adjust her immersion tone:
            </p>
            <RichTextEditor
              value={profile.diya_instructions}
              onChange={(content) => setProfile({ ...profile, diya_instructions: content })}
              placeholder="e.g. Immersion first, grammar consolidation second..."
              minHeight="110px"
            />
          </div>

          {/* Notes About Myself */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <FileText size={14} className="text-cyan-400" />
                Notes About Myself & Strategy
              </label>
            </div>
            <p className="text-xs text-slate-400 mb-2">
              Personal context, career updates, Shivani catch-up topics, other languages I know, and hobbies:
            </p>
            <RichTextEditor
              value={profile.notes}
              onChange={(content) => setProfile({ ...profile, notes: content })}
              placeholder="Career direction, guitar/piano setup, Shivani reunion in Norwich UK, other languages I know..."
              minHeight="220px"
            />
          </div>

          {/* Save Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
                saved
                  ? 'bg-emerald-600 text-white shadow-emerald-500/20'
                  : 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
              }`}
            >
              {loading ? (
                <span>Saving updates...</span>
              ) : saved ? (
                <>
                  <CheckCircle2 size={18} />
                  <span>Saved to Progress & Strategy!</span>
                </>
              ) : (
                <>
                  <Save size={18} />
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
