import React, { useState } from 'react';
import { Search, Bell, User, X, CheckCircle2, AlertCircle, Info } from 'lucide-react';

const Header = () => {
    const [showNotifications, setShowNotifications] = useState(false);
    const [notifications, setNotifications] = useState([
        { id: 1, type: 'success', text: 'ResNet-v2.4 model successfully loaded.', time: '2 mins ago' },
        { id: 2, type: 'warning', text: 'Simulation parameters outside training range.', time: '1 hour ago' },
        { id: 3, type: 'info', text: 'New documentation on LC Filters added.', time: '3 hours ago' }
    ]);

    return (
        <header className="h-16 border-b border-border bg-surface/50 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-50">
            <div className="flex items-center gap-4 bg-background/50 px-4 py-2 rounded-lg border border-white/5 w-96 transition-all focus-within:border-primary/50 focus-within:shadow-[0_0_15px_-5px_rgba(59,130,246,0.3)]">
                <Search className="w-4 h-4 text-text-muted" />
                <input
                    type="text"
                    placeholder="Search parameters, models, or benchmarks..."
                    className="bg-transparent border-none outline-none text-sm text-text-main placeholder-text-muted w-full"
                />
            </div>

            <div className="flex items-center gap-4">
                <div className="relative">
                    <button
                        onClick={() => setShowNotifications(!showNotifications)}
                        className="p-2 text-text-muted hover:text-white transition-colors relative"
                    >
                        <Bell className="w-5 h-5" />
                        {notifications.length > 0 && (
                            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-surface"></span>
                        )}
                    </button>

                    {/* Notifications Dropdown */}
                    {showNotifications && (
                        <>
                            <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)}></div>
                            <div className="absolute right-0 mt-2 w-80 bg-surface border border-border rounded-2xl shadow-2xl z-50 overflow-hidden animate-in slide-in-from-top-2 duration-200">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                                    <h3 className="font-bold text-sm text-white">Notifications</h3>
                                    <button onClick={() => setShowNotifications(false)} className="text-text-muted hover:text-white transition-colors">
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="max-h-96 overflow-y-auto scrollbar-thin">
                                    {notifications.length > 0 ? (
                                        notifications.map((notif) => (
                                            <div key={notif.id} className="p-4 border-b border-white/5 hover:bg-white/[0.02] transition-colors flex gap-3">
                                                <div className="mt-0.5">
                                                    {notif.type === 'success' && <CheckCircle2 className="w-4 h-4 text-success" />}
                                                    {notif.type === 'warning' && <AlertCircle className="w-4 h-4 text-warning" />}
                                                    {notif.type === 'info' && <Info className="w-4 h-4 text-primary" />}
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-xs text-white leading-relaxed">{notif.text}</p>
                                                    <p className="text-[10px] text-text-muted">{notif.time}</p>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-8 text-center text-text-muted text-xs">
                                            No new notifications
                                        </div>
                                    )}
                                </div>
                                <div className="p-3 bg-white/[0.02] text-center">
                                    <button
                                        onClick={() => setNotifications([])}
                                        className="text-[10px] font-bold text-primary uppercase tracking-widest hover:text-blue-400 transition-colors"
                                    >
                                        Clear All
                                    </button>
                                </div>
                            </div>
                        </>
                    )}
                </div>

                <div className="h-8 w-[1px] bg-border mx-2"></div>
                <div className="flex items-center gap-3 pl-2 pr-4 py-1.5 rounded-full hover:bg-white/5 cursor-pointer transition-colors border border-transparent hover:border-white/10">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-xs font-bold shadow-lg text-white">
                        GM
                    </div>
                    <span className="text-sm font-medium hidden md:block">Gitesh Malik</span>
                </div>
            </div>
        </header>
    );
};

export default Header;
