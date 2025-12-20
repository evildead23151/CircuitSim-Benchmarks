import React, { useState } from 'react';
import { Play, Sparkles, Activity, Gauge, AlertCircle, Info, Plus, Trash2, Layers, Settings2 } from 'lucide-react';
import { TransientChart, ErrorSweepChart } from './Charts';

const API_BASE = 'https://hot-wolves-warn.loca.lt';

const Dashboard = ({ onSimulationComplete }) => {
    const [params, setParams] = useState({
        R: 1200,
        L: 0.045,
        C: 0.000015,
        frequency: 1000,
        vin: 1.0
    });

    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [isRemote, setIsRemote] = useState(false);
    const [mode, setMode] = useState('topological'); // 'standard' or 'topological'
    const [stages, setStages] = useState([
        { tag: 1, type: 'R', value: 1200 },
        { tag: 1, type: 'L', value: 0.045 },
        { tag: 2, type: 'C', value: 0.000015 }
    ]);

    React.useEffect(() => {
        const checkStatus = async () => {
            try {
                const resp = await fetch(API_BASE, {
                    headers: { 'Bypass-Tunnel-Reminder': 'true' }
                });
                const data = await resp.json();
                setIsRemote(data.remote_active);
            } catch (e) { }
        };
        checkStatus();
    }, []);

    const runBenchmark = async () => {
        setLoading(true);
        try {
            const endpoint = mode === 'topological' ? '/benchmark/topological' : '/benchmark';
            const payload = mode === 'topological'
                ? { stages, frequency: params.frequency, vin: params.vin }
                : params;

            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Bypass-Tunnel-Reminder': 'true'
                },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (!response.ok || data.detail) {
                console.error("Benchmark error:", data);
                alert(`Simulation Failed: ${data.detail || "Unknown error"}`);
            } else {
                setResults(data);
                if (onSimulationComplete) {
                    onSimulationComplete(mode === 'topological' ? { encoding: stages.map(s => `${s.tag}(${s.type}:${s.value})`).join('-'), ...params } : params, data);
                }
            }
        } catch (e) {
            console.error("Benchmark failed", e);
            alert("Connection Failed. Check if backend is running.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Title Section */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                        Side-by-Side Comparison
                    </h2>
                    <p className="text-text-muted text-sm mt-1">Analytical Solver (SPICE) vs. AI Surrogate Model (ResNet)</p>
                </div>
                {/* Dashboard Context & OOD Alert */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${isRemote ? 'bg-orange-500/10 border-orange-500/20' : 'bg-green-500/10 border-green-500/20'}`}>
                            <div className={`w-2 h-2 rounded-full animate-pulse ${isRemote ? 'bg-orange-500' : 'bg-green-500'}`}></div>
                            <span className={`text-xs font-medium ${isRemote ? 'text-orange-400' : 'text-green-400'}`}>
                                {isRemote ? 'G-Colab Research Bridge' : 'Local LTI Analytical Solver'}
                            </span>
                        </div>
                        {results?.is_ood && (
                            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 animate-bounce">
                                <AlertCircle className="w-3 h-3 text-red-500" />
                                <span className="text-[10px] font-bold text-red-500 uppercase">OOD Warning: Bounds Exceeded</span>
                            </div>
                        )}
                    </div>
                    <div className="text-[10px] text-text-muted font-mono bg-white/5 px-3 py-1 rounded-lg border border-white/5">
                        Hardware: x64-Host-CPU | Batch: 1 | Mode: Warm-Start
                    </div>
                </div>
            </div>

            {/* Mode Switcher */}
            <div className="flex gap-1 p-1 bg-background rounded-xl border border-white/5 w-fit">
                <button
                    onClick={() => setMode('topological')}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 ${mode === 'topological' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-muted hover:text-white'}`}
                >
                    <Layers className="w-3 h-3" />
                    Topological Mode
                </button>
                <button
                    onClick={() => setMode('standard')}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 ${mode === 'standard' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-muted hover:text-white'}`}
                >
                    <Settings2 className="w-3 h-3" />
                    Standard RLC
                </button>
            </div>

            {/* Control Panel */}
            <div className="p-6 rounded-2xl bg-surface border border-border shadow-xl">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-primary" />
                        <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                            {mode === 'topological' ? 'Topological Circuit Editor' : 'Simulation Parameters'}
                        </h3>
                    </div>
                    {mode === 'topological' && (
                        <div className="flex items-center gap-2 text-[10px] font-mono text-text-muted bg-white/5 px-2 py-1 rounded">
                            Encoding: {stages.map(s => s.tag).join('')}
                        </div>
                    )}
                </div>

                {mode === 'topological' ? (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {stages.map((stage, idx) => (
                                <div key={idx} className="p-4 rounded-xl bg-background border border-white/5 relative group">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-black text-primary font-mono bg-primary/10 px-1.5 py-0.5 rounded">#{idx + 1}</span>
                                            <select
                                                value={stage.tag}
                                                onChange={(e) => {
                                                    const newStages = [...stages];
                                                    newStages[idx].tag = parseInt(e.target.value);
                                                    setStages(newStages);
                                                }}
                                                className="bg-transparent text-[10px] font-bold text-white uppercase outline-none"
                                            >
                                                <option value={1} className="bg-surface">Series</option>
                                                <option value={2} className="bg-surface">Shunt</option>
                                            </select>
                                        </div>
                                        <button
                                            onClick={() => setStages(stages.filter((_, i) => i !== idx))}
                                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:text-red-400"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex-1">
                                            <select
                                                value={stage.type}
                                                onChange={(e) => {
                                                    const newStages = [...stages];
                                                    newStages[idx].type = e.target.value;
                                                    setStages(newStages);
                                                }}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white outline-none"
                                            >
                                                <option value="R" className="bg-surface">Resistor (Ω)</option>
                                                <option value="L" className="bg-surface">Inductor (H)</option>
                                                <option value="C" className="bg-surface">Capacitor (F)</option>
                                            </select>
                                        </div>
                                        <div className="flex-1">
                                            <input
                                                type="number"
                                                value={stage.value}
                                                onChange={(e) => {
                                                    const newStages = [...stages];
                                                    newStages[idx].value = parseFloat(e.target.value);
                                                    setStages(newStages);
                                                }}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white font-mono outline-none"
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <button
                                onClick={() => setStages([...stages, { tag: 1, type: 'R', value: 100 }])}
                                className="p-4 rounded-xl border border-dashed border-white/10 hover:border-primary/50 hover:bg-primary/5 transition-all flex flex-col items-center justify-center gap-2 group"
                            >
                                <Plus className="w-6 h-6 text-text-muted group-hover:text-primary transition-colors" />
                                <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider group-hover:text-primary transition-colors">Add Component</span>
                            </button>
                        </div>

                        <div className="pt-6 border-t border-white/5 grid grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-text-muted uppercase">Global Frequency (Hz)</label>
                                <input
                                    type="number"
                                    value={params.frequency}
                                    onChange={(e) => setParams({ ...params, frequency: parseFloat(e.target.value) })}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono outline-none focus:border-primary"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-text-muted uppercase">Input Voltage (V)</label>
                                <input
                                    type="number"
                                    value={params.vin}
                                    onChange={(e) => setParams({ ...params, vin: parseFloat(e.target.value) })}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono outline-none focus:border-primary"
                                />
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        {[
                            { label: 'Resistance (Ω)', key: 'R', min: 10, max: 2000, step: 10 },
                            { label: 'Inductance (H)', key: 'L', min: 0.001, max: 0.1, step: 0.001 },
                            { label: 'Capacitance (F)', key: 'C', min: 1e-6, max: 1e-4, step: 1e-7 },
                            { label: 'Frequency (Hz)', key: 'frequency', min: 10, max: 10000, step: 10 }
                        ].map((field) => (
                            <div key={field.key} className="space-y-2">
                                <div className="flex justify-between">
                                    <label className="text-xs font-medium text-text-muted uppercase">{field.label}</label>
                                    <span className="text-xs text-primary font-mono">{params[field.key]}</span>
                                </div>
                                <input
                                    type="range"
                                    min={field.min} max={field.max} step={field.step}
                                    value={params[field.key]}
                                    onChange={(e) => setParams({ ...params, [field.key]: parseFloat(e.target.value) })}
                                    className="w-full h-2 bg-background rounded-lg appearance-none cursor-pointer accent-primary hover:accent-blue-400 transition-all border border-white/5"
                                />
                                <div className="flex justify-between px-1">
                                    <input
                                        type="number"
                                        value={params[field.key]}
                                        onChange={(e) => {
                                            const val = parseFloat(e.target.value);
                                            setParams({ ...params, [field.key]: isNaN(val) ? 0 : val });
                                        }}
                                        className="w-full bg-transparent border-none text-xs text-text-muted font-mono focus:text-white focus:outline-none"
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <div className="mt-8 flex justify-end">
                    <button
                        onClick={runBenchmark}
                        disabled={loading}
                        className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-blue-600 active:scale-95 text-white font-semibold rounded-lg shadow-[0_0_20px_-5px_rgba(59,130,246,0.5)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        ) : (
                            <Play className="w-5 h-5 fill-current" />
                        )}
                        Run Comparison
                    </button>
                </div>
            </div>

            {/* Results Section - Conditional on results existing */}
            {results && (<>
                {/* Results Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Comparison Card */}
                    <div className="lg:col-span-2 p-8 rounded-3xl bg-surface border border-border relative overflow-hidden group">
                        <div className="flex justify-between items-start mb-10">
                            <div>
                                <h3 className="text-xl font-black text-white tracking-widest uppercase">Inference Validation</h3>
                                <p className="text-[10px] text-text-muted mt-1 font-mono">Comparing Analytical Ground Truth vs Neural Surrogate</p>
                            </div>
                            <div className="px-3 py-2 rounded-xl bg-background border border-border flex flex-col items-end">
                                <span className="text-[9px] text-text-muted uppercase font-bold tracking-tighter">Speed Factor</span>
                                <span className="text-2xl font-mono font-black text-primary italic">
                                    {results ? results.speed_factor.toFixed(1) : '1.0'}x
                                </span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                            {/* Analytical Ground Truth */}
                            <div className="relative">
                                <div className="flex items-center gap-2 text-text-muted mb-4">
                                    <span className="text-[9px] font-black uppercase tracking-widest bg-white/5 px-2 py-1 rounded">Solver v3.0 (Deep Theory)</span>
                                </div>
                                <div className="space-y-1">
                                    <div className="text-5xl font-mono font-black text-white flex items-baseline gap-2">
                                        {results ? results.solver_vout.toFixed(4) : '0.0000'}
                                        <span className="text-sm text-text-muted font-normal">V</span>
                                    </div>
                                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Analytical Solver Vout</div>
                                </div>
                                <div className="mt-6 flex flex-col pt-4 border-t border-white/5">
                                    <span className="text-[9px] text-text-muted uppercase font-bold">Latency (Average Warm-start)</span>
                                    <span className="text-xs font-mono text-white mt-1">
                                        {results ? results.solver_time_ms.toFixed(4) : '--'} ms
                                    </span>
                                </div>
                            </div>

                            {/* Research Transparency Card */}
                            <div className="md:col-span-1 p-6 rounded-2xl bg-surface/50 border border-white/5 flex flex-col justify-between">
                                <div>
                                    <div className="flex items-center gap-2 mb-4 text-primary">
                                        <Info className="w-4 h-4" />
                                        <span className="text-[10px] font-bold uppercase tracking-widest">Research Metrics</span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <div className="text-[9px] text-text-muted font-bold uppercase mb-1">Input Current (In)</div>
                                            <div className="text-xl font-black text-white">
                                                {results.iin_ma.toFixed(2)}<span className="text-[10px] text-text-muted ml-0.5">mA</span>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-[9px] text-text-muted font-bold uppercase mb-1">Energy Efficiency</div>
                                            <div className="text-xl font-black text-green-400">
                                                {(results.efficiency * 100).toFixed(1)}%
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-[9px] text-text-muted font-bold uppercase mb-1">Rise Time (tr)</div>
                                            <div className="text-xl font-black text-blue-400">
                                                {results.rise_time_ms.toFixed(3)}<span className="text-[10px] text-text-muted ml-0.5">ms</span>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-[9px] text-text-muted font-bold uppercase mb-1">Peak Overshoot</div>
                                            <div className="text-xl font-black text-orange-400">
                                                {results.overshoot_pct.toFixed(1)}%
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="mt-6 pt-4 border-t border-white/5">
                                    <p className="text-[10px] leading-relaxed text-text-muted italic">
                                        Note: Solver v3.0 incorporates <strong>Non-Ideal Parasitics</strong> (ESR/Leakage) as per Alexander/Sadiku.
                                        Transient metrics represent a 1V step switching state.
                                    </p>
                                </div>
                            </div>

                            {/* ML Surrogate */}
                            <div className={`p-6 rounded-2xl border transition-all ${results?.is_ood ? 'bg-red-500/5 border-red-500/20 shadow-lg shadow-red-500/5' : 'bg-primary/5 border-primary/20 shadow-lg shadow-primary/5'}`}>
                                <div className="flex items-center justify-between mb-6">
                                    <span className={`text-[9px] font-black uppercase tracking-widest ${results?.is_ood ? 'text-red-500' : 'text-primary'}`}>MLP Regressor</span>
                                    {results?.ai_source === 'remote' && <span className="px-1 py-0.5 bg-orange-500/10 text-orange-400 text-[8px] font-black rounded border border-orange-500/20 uppercase">Research Proxy</span>}
                                </div>
                                <div className="space-y-1">
                                    <div className={`text-5xl font-mono font-black flex items-baseline gap-2 ${results?.is_ood ? 'text-red-400 opacity-60' : 'text-primary'}`}>
                                        {results ? results.ai_vout.toFixed(4) : '0.0000'}
                                        <span className="text-sm text-text-muted font-normal">V</span>
                                    </div>
                                    <div className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Surrogate Prediction</div>
                                </div>
                                <div className="mt-8 grid grid-cols-2 gap-4">
                                    <div className="flex flex-col">
                                        <span className="text-[9px] text-text-muted uppercase font-bold">Inference Time</span>
                                        <span className={`text-xs font-mono ${results?.is_ood ? 'text-red-400' : 'text-white'}`}>
                                            {results ? results.ai_time_ms.toFixed(4) : '--'} ms
                                        </span>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-[9px] text-text-muted uppercase font-bold">Relative Error</span>
                                        <span className={`text-xs font-mono font-black ${results?.error_percent > 2 ? 'text-warning' : (results?.is_ood ? 'text-red-400' : 'text-success')}`}>
                                            {results ? results.error_percent.toFixed(2) : '0.00'}%
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Accuracy Distribution Panel */}
                    <div className="p-8 rounded-3xl bg-surface border border-border flex flex-col">
                        <h4 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-6 border-b border-border pb-4">Validation Context</h4>
                        <div className="flex-1 space-y-8">
                            <div>
                                <div className="flex justify-between items-end mb-2">
                                    <span className="text-[10px] text-white font-bold uppercase">Mean Absolute Error</span>
                                    <span className="text-sm font-mono text-primary">{results ? (results.error_abs * 1000).toFixed(2) : '--'} mV</span>
                                </div>
                                <div className="h-1 w-full bg-background rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-500 ${results?.error_percent > 1 ? 'bg-warning' : 'bg-primary'}`}
                                        style={{ width: `${Math.min(results?.error_percent * 20 || 0, 100)}%` }}
                                    />
                                </div>
                            </div>

                            <div className="p-4 rounded-xl bg-background/50 border border-white/5 space-y-3">
                                <h5 className="text-[9px] font-bold text-white uppercase tracking-tighter">System Assumptions</h5>
                                <ul className="space-y-1.5">
                                    <li className="text-[8px] text-text-muted flex items-start gap-1.5 uppercase tracking-tighter">
                                        <div className="w-1 h-1 rounded-full bg-primary mt-1" />
                                        Steady-State AC Analysis Only
                                    </li>
                                    <li className="text-[8px] text-text-muted flex items-start gap-1.5 uppercase tracking-tighter">
                                        <div className="w-1 h-1 rounded-full bg-primary mt-1" />
                                        Ideal Passive Components
                                    </li>
                                    <li className="text-[8px] text-text-muted flex items-start gap-1.5 uppercase tracking-tighter">
                                        <div className="w-1 h-1 rounded-full bg-primary mt-1" />
                                        No non-linear/switching dynamics
                                    </li>
                                </ul>
                            </div>
                        </div>
                        <div className="mt-auto pt-6">
                            <div className={`p-4 rounded-2xl border text-[9px] font-medium leading-relaxed uppercase tracking-tight ${results?.is_ood ? 'bg-red-500/10 border-red-500/20 text-red-500' : 'bg-blue-500/5 border-blue-500/10 text-text-muted'}`}>
                                {results?.is_ood
                                    ? "Critical: Prediction reliability low. Hardware components exceed training profile bounds. Physics-only analysis recommended."
                                    : "Prediction within nominal bounds. AI surrogate accuracy verified against ground truth."
                                }
                            </div>
                        </div>
                    </div>
                </div>

                {/* Scientific Transparency Panel */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                    <TransientChart
                        physicsVout={results?.solver_vout || 0}
                        aiVout={results?.ai_vout || 0}
                        frequency={params.frequency}
                    />
                    <ErrorSweepChart />
                </div>

                <div className="mt-8 p-6 rounded-2xl bg-surface border border-border">
                    <div className="flex items-center gap-2 mb-4">
                        <Info className="w-4 h-4 text-primary" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest">Model & Solver Methodology</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-[10px]">
                        <div className="space-y-2 p-4 bg-background/50 rounded-xl border border-white/5">
                            <span className="text-primary font-bold uppercase tracking-tighter text-[9px]">A. Analytical Solver</span>
                            <p className="text-text-muted leading-relaxed">
                                Uses closed-form LTI equations for impedance mapping. Ground truth is strictly valid for linear, frequency-stable circuits. No SPICE transient analysis is currently implemented.
                            </p>
                        </div>
                        <div className="space-y-2 p-4 bg-background/50 rounded-xl border border-white/5">
                            <span className="text-primary font-bold uppercase tracking-tighter text-[9px]">B. Surrogate Architecture</span>
                            <p className="text-text-muted leading-relaxed">
                                MLP Regressor trained on 10k samples. Targets log10-domain voltage responses to preserve resolution across orders of magnitude. Input vectors: [R, L, C].
                            </p>
                        </div>
                        <div className="space-y-2 p-4 bg-background/50 rounded-xl border border-white/5">
                            <span className="text-primary font-bold uppercase tracking-tighter text-[9px]">C. Benchmarking Protocol</span>
                            <p className="text-text-muted leading-relaxed">
                                Speed factors calculated using Warm-Start CPU averages. Latency includes inference overhead but excludes model-load startup time (scientifically isolated).
                            </p>
                        </div>
                    </div>
                </div>
            </>)}

            {/* Placeholder visuals if no results yet */}
            {!results && (
                <div className="p-12 text-center border border-dashed border-white/10 rounded-2xl bg-white/5 mx-auto">
                    <Gauge className="w-12 h-12 text-text-muted mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium text-white">Ready for Simulation</h3>
                    <p className="text-text-muted max-w-md mx-auto mt-2">
                        Adjust the parameters above and click "Run Comparison" to see real-time benchmarking between the analytical physics solver and the neural network surrogate.
                    </p>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
