import React from 'react';
import { LayoutDashboard, Activity, Database, Settings, BookOpen, Cpu } from 'lucide-react';

const Sidebar = ({ activePage, onNavigate }) => {
    const navItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Simulator' },
        { id: 'benchmarks', icon: Activity, label: 'History' },
        { id: 'models', icon: Database, label: 'Models' },
        { id: 'docs', icon: BookOpen, label: 'Documentation' },
        { id: 'settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <aside className="w-64 bg-surface border-r border-border flex flex-col">
            <div className="p-6 flex items-center gap-3 border-b border-border/50">
                <div className="p-2 bg-primary/20 rounded-lg">
                    <Cpu className="w-6 h-6 text-primary" />
                </div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                    CircuitSim
                </h1>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                            ${activePage === item.id
                                ? 'bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_-3px_rgba(59,130,246,0.2)]'
                                : 'text-text-muted hover:bg-white/5 hover:text-white'
                            }`}
                    >
                        <item.icon className="w-5 h-5" />
                        <span className="font-medium">{item.label}</span>
                    </button>
                ))}
            </nav>

            <div className="p-4 m-4 rounded-xl bg-gradient-to-br from-secondary/20 to-primary/20 border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span className="text-xs font-medium text-green-400">System Online</span>
                </div>
                <p className="text-xs text-text-muted">v2.4.0 (Stable)</p>
            </div>
        </aside>
    );
};

export default Sidebar;
