import React from 'react';
import { motion } from 'framer-motion';
import {
    Zap,
    ShieldCheck,
    ChevronRight,
    Github,
    Activity,
    Cpu,
    Layers,
    ArrowRight
} from 'lucide-react';

const Home = ({ onNavigate }) => {
    return (
        <div className="min-h-screen bg-background text-text-main overflow-x-hidden">
            {/* Header / Nav */}
            <nav className="flex items-center justify-between px-8 py-6 border-b border-white/5 bg-background/50 backdrop-blur-md sticky top-0 z-50">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                        <Zap className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl font-bold tracking-tight text-white">CircuitBenchmark</span>
                </div>

                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-text-muted">
                    <button onClick={() => onNavigate('docs')} className="hover:text-primary transition-colors">Methodology</button>
                    <button onClick={() => onNavigate('benchmarks')} className="hover:text-primary transition-colors">Benchmarks</button>
                    <button onClick={() => {
                        const el = document.getElementById('core-principles');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                    }} className="hover:text-primary transition-colors">About</button>
                </div>

                <button className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-all text-sm font-bold text-white">
                    <Github className="w-4 h-4" />
                    GitHub Repo
                </button>
            </nav>

            {/* Hero Section */}
            <section className="px-8 pt-20 pb-32 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8 }}
                    className="space-y-8"
                >
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                        <span className="text-[10px] font-bold text-primary uppercase tracking-widest">v2.0 Benchmark Live</span>
                    </div>

                    <h1 className="text-6xl md:text-7xl font-extrabold tracking-tighter leading-none text-white">
                        AI vs Physics:<br />
                        <span className="text-primary italic">Circuit Modeling</span>
                    </h1>

                    <p className="text-xl text-text-muted leading-relaxed max-w-xl">
                        Comparing analytical circuit equations with machine learning surrogate models for next-gen electronics design.
                    </p>

                    <div className="flex flex-wrap gap-4">
                        <button
                            onClick={() => onNavigate('dashboard')}
                            className="px-8 py-4 bg-primary text-white font-bold rounded-xl hover:bg-blue-600 transition-all flex items-center gap-2 group shadow-lg shadow-primary/20"
                        >
                            Try the Simulator
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </button>
                        <button
                            onClick={() => onNavigate('benchmarks')}
                            className="px-8 py-4 bg-white/5 border border-white/10 text-white font-bold rounded-xl hover:bg-white/10 transition-all"
                        >
                            View Comparison Results
                        </button>
                    </div>

                    <div className="flex items-center gap-8 pt-4">
                        <div className="flex items-center gap-2 text-sm text-text-muted">
                            <ShieldCheck className="w-5 h-5 text-primary" />
                            SPICE-Validated
                        </div>
                        <div className="flex items-center gap-2 text-sm text-text-muted">
                            <Zap className="w-5 h-5 text-primary" />
                            &lt;1ms Inference
                        </div>
                    </div>
                </motion.div>

                {/* Right Visual: Comparison Pane */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className="relative aspect-square md:aspect-video lg:aspect-square bg-surface border border-border rounded-[2rem] overflow-hidden shadow-2xl flex"
                >
                    {/* Analytical Side */}
                    <div className="flex-1 border-r border-white/5 p-8 flex flex-col justify-between bg-background/30 backdrop-blur-sm relative overflow-hidden">
                        <div className="absolute inset-0 opacity-10 flex items-center justify-center p-12">
                            <Cpu className="w-full h-full text-white" />
                        </div>
                        <span className="px-3 py-1 bg-white/10 border border-white/10 rounded font-mono text-[10px] text-white self-start uppercase tracking-widest relative">Analytical</span>
                        <div className="space-y-4 relative">
                            <div className="font-mono text-xs text-text-muted space-y-1">
                                <div className="text-primary">V(t) = L * di/dt</div>
                                <div>I(t) = C * dv/dt</div>
                                <div>Z = R + jωL + 1/jωC</div>
                            </div>
                            <h3 className="text-xl font-bold text-white tracking-tight leading-tight">Differential Eq.<br />Solver</h3>
                        </div>
                    </div>

                    {/* VS Badge */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-12 h-12 bg-primary rounded-full border-4 border-background flex items-center justify-center text-xs font-black text-white italic shadow-lg shadow-primary/20">
                        VS
                    </div>

                    {/* Surrogate Side */}
                    <div className="flex-1 p-8 flex flex-col justify-between bg-primary/5 relative overflow-hidden">
                        <div className="absolute inset-0 opacity-10 flex items-center justify-center overflow-hidden">
                            <div className="w-full h-1 bg-primary relative animate-pulse shadow-[0_0_20px_rgba(59,130,246,0.5)] rotate-[-15deg]"></div>
                        </div>
                        <span className="px-3 py-1 bg-primary/20 border border-primary/20 rounded font-mono text-[10px] text-primary self-end uppercase tracking-widest relative">Surrogate Model</span>
                        <div className="space-y-4 relative">
                            <div className="flex items-end gap-1 h-12">
                                {[0.4, 0.7, 0.5, 0.9, 0.6, 0.8, 0.4, 0.7].map((h, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ height: 0 }}
                                        animate={{ height: `${h * 100}%` }}
                                        transition={{ duration: 1, delay: 0.5 + (i * 0.1), repeat: Infinity, repeatType: 'reverse' }}
                                        className="w-2 bg-primary rounded-t-sm"
                                    />
                                ))}
                            </div>
                            <h3 className="text-xl font-bold text-white tracking-tight leading-tight">Deep Neural<br />Network</h3>
                        </div>
                    </div>
                </motion.div>
            </section>

            {/* Core Principles */}
            <section id="core-principles" className="px-8 py-32 bg-surface/30 border-y border-white/5">
                <div className="max-w-7xl mx-auto space-y-20">
                    <div className="text-center space-y-4">
                        <h2 className="text-4xl font-bold text-white">Core Principles</h2>
                        <p className="text-text-muted max-w-2xl mx-auto">Built on transparency and rigorous validation against ground-truth physics simulations.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                        {[
                            {
                                icon: ShieldCheck,
                                title: 'Accuracy First',
                                desc: 'Every AI model is benchmarked across 10,000+ corner cases in SPICE before deployment.'
                            },
                            {
                                icon: Zap,
                                title: 'Sub-ms Latency',
                                desc: 'Replace slow iterative solvers with instant neural inference for real-time design exploration.'
                            },
                            {
                                icon: Layers,
                                title: 'Model Agnostic',
                                desc: 'Compare ResNets, Transformers, or Simple MLPs against traditional nodal analysis.'
                            }
                        ].map((feature, idx) => (
                            <div key={idx} className="space-y-4 group p-6 rounded-2xl hover:bg-white/[0.02] transition-colors border border-transparent hover:border-white/5">
                                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                                    <feature.icon className="w-6 h-6" />
                                </div>
                                <h3 className="text-xl font-bold text-white">{feature.title}</h3>
                                <p className="text-text-muted leading-relaxed text-sm">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="px-8 py-12 border-t border-white/5 text-center space-y-4">
                <div className="flex items-center justify-center gap-2 opacity-50">
                    <Zap className="w-4 h-4 text-primary" />
                    <span className="text-sm font-bold tracking-tight text-white uppercase">CircuitSim Research</span>
                </div>
                <p className="text-[10px] text-text-muted uppercase tracking-[0.2em] font-medium">© 2025 Deep Learning Electronics Design Group</p>
            </footer>
        </div>
    );
};

export default Home;
