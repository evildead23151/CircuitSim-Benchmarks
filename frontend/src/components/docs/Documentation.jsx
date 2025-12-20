import React from 'react';
import {
    BookOpen,
    Lightbulb,
    FileText,
    Target,
    ShieldCheck,
    ChevronRight,
    Terminal,
    Dna,
    Zap
} from 'lucide-react';

const Documentation = () => {
    return (
        <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Hero Section */}
            <div className="text-center space-y-4 pt-8">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider">
                    <BookOpen className="w-3 h-3" />
                    Knowledge Base
                </div>
                <h1 className="text-4xl font-extrabold text-white tracking-tight">CircuitSim Internal Specs</h1>
                <p className="text-text-muted text-lg max-w-2xl mx-auto">
                    A research-grade environment comparing deterministic physics solvers against deep learning surrogate models.
                </p>
            </div>

            {/* Quick Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { title: 'The Physics Engine', icon: ShieldCheck, desc: 'SPICE-accurate frequency response formulas.' },
                    { title: 'AI Surrogates', icon: Dna, desc: 'Model architecture and training distribution.' },
                    { title: 'Benchmark API', icon: Terminal, desc: 'How metrics like Accuracy and Speedup are calculated.' }
                ].map((item, idx) => (
                    <div key={idx} className="p-6 rounded-2xl bg-surface border border-border hover:border-primary/30 transition-all group cursor-pointer">
                        <item.icon className="w-6 h-6 text-primary mb-4 group-hover:scale-110 transition-transform" />
                        <h3 className="text-white font-bold mb-2">{item.title}</h3>
                        <p className="text-text-muted text-xs leading-relaxed">{item.desc}</p>
                    </div>
                ))}
            </div>

            {/* Core Sections */}
            <div className="space-y-10 pb-20">
                <section className="space-y-6">
                    <div className="flex items-center gap-2 border-b border-border pb-4">
                        <Target className="w-5 h-5 text-primary" />
                        <h2 className="text-2xl font-bold text-white uppercase tracking-tight">1. Deterministic Physics (Ground Truth)</h2>
                    </div>
                    <div className="prose prose-invert max-w-none text-text-muted space-y-4">
                        <p>
                            The core simulation uses standard AC steady-state analysis for Second-Order RLC filters. Our solver calculates the transfer function <strong>H(s)</strong> based on the selected topology.
                        </p>
                        <div className="p-6 rounded-xl bg-background border border-white/5 font-mono text-center text-primary italic">
                            Vout(ω) = Vin / √[ (1 - ω²LC)² + (ωRC)² ]
                        </div>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 list-none p-0">
                            {[
                                'Ideal passive components (No ESR/ESL)',
                                'Linear small-signal approximation',
                                'Complex impedance vectorization',
                                'Fixed 1kHz carrier frequency'
                            ].map((li, i) => (
                                <li key={i} className="flex items-center gap-2 text-xs bg-white/5 p-3 rounded-lg border border-white/5">
                                    <ChevronRight className="w-3 h-3 text-primary" />
                                    {li}
                                </li>
                            ))}
                        </ul>
                    </div>
                </section>

                <section className="space-y-6">
                    <div className="flex items-center gap-2 border-b border-border pb-4">
                        <Lightbulb className="w-5 h-5 text-yellow-500" />
                        <h2 className="text-2xl font-bold text-white uppercase tracking-tight">2. Neural Surrogate Model (AI)</h2>
                    </div>
                    <div className="prose prose-invert max-w-none text-text-muted space-y-4">
                        <p>
                            Instead of solving differential equations, we use a pre-trained Regression model that "knows" the physics by heart.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="p-5 rounded-2xl bg-surface border border-border">
                                <h4 className="text-white font-bold mb-3 flex items-center gap-2 text-sm">
                                    <FileText className="w-4 h-4 text-primary" />
                                    Input Contract
                                </h4>
                                <p className="text-[11px] leading-relaxed mb-4">The model expects normalized feature vectors representing circuit components.</p>
                                <div className="space-y-2 font-mono text-[10px]">
                                    <div className="flex justify-between p-2 bg-background rounded"><span>R_ohm</span> <span className="text-primary">[10, 1000]</span></div>
                                    <div className="flex justify-between p-2 bg-background rounded"><span>L_henry</span> <span className="text-primary">[1u, 100m]</span></div>
                                    <div className="flex justify-between p-2 bg-background rounded"><span>C_farad</span> <span className="text-primary">[1n, 100u]</span></div>
                                </div>
                            </div>
                            <div className="p-5 rounded-2xl bg-surface border border-border">
                                <h4 className="text-white font-bold mb-3 flex items-center gap-2 text-sm">
                                    <Target className="w-4 h-4 text-success" />
                                    Output Target
                                </h4>
                                <p className="text-[11px] leading-relaxed mb-4">To handle wide dynamic ranges (mV to V), the model predicts Log-Voltage.</p>
                                <div className="p-4 bg-background rounded font-mono text-[10px] space-y-2">
                                    <div className="text-text-muted"># Transformation</div>
                                    <div className="text-primary">Vout_real = Power(10, prediction)</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="p-8 rounded-3xl bg-primary/10 border border-primary/20 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-125 transition-transform">
                        <Zap className="w-32 h-32 text-primary" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Notice to Researchers</h3>
                    <p className="text-text-muted text-sm max-w-xl leading-relaxed">
                        While the AI model is <strong>99.4% accurate</strong> within standard ranges, it lacks the generalizability of physical laws. If you operate outside the training distribution (as warned in the Workbench), results may diverge significantly.
                    </p>
                </section>
            </div>
        </div>
    );
};

export default Documentation;
