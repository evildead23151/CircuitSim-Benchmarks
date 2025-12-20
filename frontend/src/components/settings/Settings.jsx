import React, { useState } from 'react';
import {
    Settings as SettingsIcon,
    Bell,
    Shield,
    Link2,
    Database,
    Palette,
    FileJson,
    Save
} from 'lucide-react';

const Settings = () => {
    const [settings, setSettings] = useState({
        apiUrl: 'http://localhost:8000',
        autoSolve: true,
        highPrecision: false,
        notifications: true,
        theme: 'dark-cyber',
        saveHistory: true
    });

    const handleSave = () => {
        alert("Configuration Saved to LocalStorage!");
    };

    return (
        <div className="max-w-4xl space-y-8 animate-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div>
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-xl bg-primary/10">
                        <SettingsIcon className="w-5 h-5 text-primary" />
                    </div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">System Settings</h2>
                </div>
                <p className="text-text-muted">Manage your research environment, API bridges, and global simulation parameters.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Connection Settings */}
                <div className="p-6 rounded-2xl bg-surface border border-border space-y-6">
                    <div className="flex items-center gap-2 mb-2">
                        <Link2 className="w-4 h-4 text-primary" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Connections</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs text-text-muted">Backend API URL</label>
                            <input
                                value={settings.apiUrl}
                                onChange={(e) => setSettings({ ...settings, apiUrl: e.target.value })}
                                className="w-full bg-background border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:border-primary outline-none transition-all"
                            />
                        </div>
                        <div className="flex items-center justify-between p-4 rounded-xl bg-background/50 border border-white/5">
                            <div className="space-y-1">
                                <span className="text-xs font-bold text-white">Auto-Solve Toggle</span>
                                <p className="text-[10px] text-text-muted">Run simulation instantly on parameter change.</p>
                            </div>
                            <button
                                onClick={() => setSettings({ ...settings, autoSolve: !settings.autoSolve })}
                                className={`w-10 h-5 rounded-full relative transition-all ${settings.autoSolve ? 'bg-primary' : 'bg-white/10'}`}
                            >
                                <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${settings.autoSolve ? 'left-6' : 'left-1'}`} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Simulation Engine */}
                <div className="p-6 rounded-2xl bg-surface border border-border space-y-6">
                    <div className="flex items-center gap-2 mb-2">
                        <Database className="w-4 h-4 text-secondary" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Physics Engine</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 rounded-xl bg-background/50 border border-white/5">
                            <div className="space-y-1">
                                <span className="text-xs font-bold text-white">Double Precision (64-bit)</span>
                                <p className="text-[10px] text-text-muted">High accuracy solving, slightly slower.</p>
                            </div>
                            <button
                                onClick={() => setSettings({ ...settings, highPrecision: !settings.highPrecision })}
                                className={`w-10 h-5 rounded-full relative transition-all ${settings.highPrecision ? 'bg-secondary' : 'bg-white/10'}`}
                            >
                                <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${settings.highPrecision ? 'left-6' : 'left-1'}`} />
                            </button>
                        </div>
                        <div className="flex items-center justify-between p-4 rounded-xl bg-background/50 border border-white/5">
                            <div className="space-y-1">
                                <span className="text-xs font-bold text-white">Cache Results</span>
                                <p className="text-[10px] text-text-muted">Save previous runs to local storage.</p>
                            </div>
                            <button
                                onClick={() => setSettings({ ...settings, saveHistory: !settings.saveHistory })}
                                className={`w-10 h-5 rounded-full relative transition-all ${settings.saveHistory ? 'bg-secondary' : 'bg-white/10'}`}
                            >
                                <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${settings.saveHistory ? 'left-6' : 'left-1'}`} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Notifications & Security */}
                <div className="p-6 rounded-2xl bg-surface border border-border space-y-6">
                    <div className="flex items-center gap-2 mb-2">
                        <Shield className="w-4 h-4 text-success" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Security & Alerts</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 rounded-xl bg-background/50 border border-white/5">
                            <div className="flex items-center gap-3">
                                <Bell className="w-4 h-4 text-text-muted" />
                                <span className="text-xs font-bold text-white">Browser Notifications</span>
                            </div>
                            <button
                                onClick={() => setSettings({ ...settings, notifications: !settings.notifications })}
                                className={`w-10 h-5 rounded-full relative transition-all ${settings.notifications ? 'bg-success' : 'bg-white/10'}`}
                            >
                                <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${settings.notifications ? 'left-6' : 'left-1'}`} />
                            </button>
                        </div>
                        <button className="w-full py-3 bg-background/50 border border-white/5 rounded-xl text-xs text-white hover:bg-white/10 transition-all flex items-center justify-center gap-2">
                            <FileJson className="w-3 h-3" />
                            Export Data (.json)
                        </button>
                    </div>
                </div>

                {/* Appearance */}
                <div className="p-6 rounded-2xl bg-surface border border-border space-y-6">
                    <div className="flex items-center gap-2 mb-2">
                        <Palette className="w-4 h-4 text-warning" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Appearance</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs text-text-muted">Color Palette</label>
                            <select
                                value={settings.theme}
                                onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
                                className="w-full bg-background border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:border-warning outline-none transition-all appearance-none"
                            >
                                <option value="dark-cyber">Cyber Dark (Default)</option>
                                <option value="midnight">Midnight Blue</option>
                                <option value="academic">Academic Gray</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end pt-4">
                <button
                    onClick={handleSave}
                    className="flex items-center gap-2 px-8 py-3 bg-primary text-white font-bold rounded-xl hover:bg-blue-600 transition-all shadow-lg shadow-primary/20"
                >
                    <Save className="w-4 h-4" />
                    Apply Settings
                </button>
            </div>
        </div>
    );
};

export default Settings;
