import React, { useState, useEffect } from 'react';
import {
    BarChart3,
    Zap,
    Clock,
    TrendingUp,
    AlertCircle,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Info
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const API_BASE = 'https://hot-wolves-warn.loca.lt';

const MODEL_COLORS = {
    random_forest: '#6366f1',
    mlp: '#22c55e',
    pinn: '#f59e0b',
    deeponet: '#ec4899',
    fno: '#06b6d4',
    ensemble: '#a855f7',
};

const MODEL_LABELS = {
    random_forest: 'Random Forest',
    mlp: 'MLP',
    pinn: 'PINN',
    deeponet: 'DeepONet',
    fno: 'FNO',
    ensemble: 'Ensemble',
};

const DEFAULT_STAGES = [
    { tag: 1, type: 'R', value: 1200 },
    { tag: 1, type: 'L', value: 0.045 },
    { tag: 2, type: 'C', value: 0.000015 },
];

const ModelComparisonDashboard = () => {
    const [models, setModels] = useState([]);
    const [compareResults, setCompareResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [listLoading, setListLoading] = useState(false);
    const [error, setError] = useState(null);
    const [frequency, setFrequency] = useState(1000);
    const [vin, setVin] = useState(1.0);

    const fetchModels = async () => {
        setListLoading(true);
        setError(null);
        try {
            const resp = await fetch(`${API_BASE}/models/list`, {
                headers: { 'Bypass-Tunnel-Reminder': 'true' }
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            setModels(data.models || []);
        } catch (e) {
            setError(`Failed to fetch model list: ${e.message}`);
        } finally {
            setListLoading(false);
        }
    };

    const runComparison = async () => {
        setLoading(true);
        setError(null);
        try {
            const payload = {
                stages: DEFAULT_STAGES,
                frequency,
                vin,
            };
            const resp = await fetch(`${API_BASE}/models/compare`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Bypass-Tunnel-Reminder': 'true'
                },
                body: JSON.stringify(payload),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            setCompareResults(Array.isArray(data) ? data : []);
        } catch (e) {
            setError(`Comparison failed: ${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchModels();
    }, []);

    const chartData = compareResults.map(r => ({
        name: MODEL_LABELS[r.model_name] || r.model_name,
        model_name: r.model_name,
        vout: parseFloat((r.vout ?? 0).toFixed(6)),
        latency_ms: parseFloat((r.latency_ms ?? 0).toFixed(3)),
        error_pct: parseFloat((r.error_pct ?? 0).toFixed(3)),
    }));

    const radarData = compareResults.map(r => ({
        model: MODEL_LABELS[r.model_name] || r.model_name,
        Speed: r.latency_ms > 0 ? Math.min(100, 10 / r.latency_ms * 100) : 0,
        Accuracy: r.error_pct !== undefined ? Math.max(0, 100 - r.error_pct * 10) : 50,
        Available: r.available ? 100 : 0,
    }));

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-text-main flex items-center gap-2">
                        <BarChart3 className="text-primary" size={28} />
                        Model Comparison Dashboard
                    </h2>
                    <p className="text-text-muted text-sm mt-1">
                        Compare all surrogate models side-by-side on the same circuit
                    </p>
                </div>
                <button
                    onClick={fetchModels}
                    disabled={listLoading}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface border border-border text-text-muted hover:text-text-main transition-colors"
                >
                    <RefreshCw size={16} className={listLoading ? 'animate-spin' : ''} />
                    Refresh
                </button>
            </div>

            {/* Error banner */}
            {error && (
                <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                    <AlertCircle size={18} />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            {/* Model registry table */}
            <div className="bg-surface border border-border rounded-xl p-5">
                <h3 className="font-semibold text-text-main mb-3 flex items-center gap-2">
                    <Info size={16} className="text-primary" />
                    Available Surrogate Models
                </h3>
                {listLoading ? (
                    <div className="text-text-muted text-sm animate-pulse">Loading model registry…</div>
                ) : models.length === 0 ? (
                    <div className="text-text-muted text-sm">No models registered. Backend may not be reachable.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-text-muted border-b border-border">
                                    <th className="text-left py-2 pr-4">Model</th>
                                    <th className="text-left py-2 pr-4">Type</th>
                                    <th className="text-left py-2 pr-4">Status</th>
                                    <th className="text-left py-2">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                {models.map(m => (
                                    <tr key={m.name} className="border-b border-border/50 hover:bg-white/5">
                                        <td className="py-2 pr-4 font-mono font-medium" style={{ color: MODEL_COLORS[m.name] || '#94a3b8' }}>
                                            {MODEL_LABELS[m.name] || m.name}
                                        </td>
                                        <td className="py-2 pr-4 text-text-muted">{m.type || '—'}</td>
                                        <td className="py-2 pr-4">
                                            {m.available ? (
                                                <span className="flex items-center gap-1 text-green-400">
                                                    <CheckCircle2 size={14} /> Ready
                                                </span>
                                            ) : (
                                                <span className="flex items-center gap-1 text-yellow-500">
                                                    <XCircle size={14} /> No weights
                                                </span>
                                            )}
                                        </td>
                                        <td className="py-2 text-text-muted text-xs">{m.description || '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Comparison controls */}
            <div className="bg-surface border border-border rounded-xl p-5">
                <h3 className="font-semibold text-text-main mb-4 flex items-center gap-2">
                    <Zap size={16} className="text-primary" />
                    Run Comparison
                </h3>
                <div className="flex flex-wrap gap-4 items-end">
                    <div>
                        <label className="block text-xs text-text-muted mb-1">Frequency (Hz)</label>
                        <input
                            type="number"
                            value={frequency}
                            onChange={e => setFrequency(Number(e.target.value))}
                            className="w-32 px-3 py-2 bg-background border border-border rounded-lg text-text-main text-sm focus:border-primary outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-text-muted mb-1">Vin (V)</label>
                        <input
                            type="number"
                            value={vin}
                            onChange={e => setVin(Number(e.target.value))}
                            step="0.1"
                            className="w-24 px-3 py-2 bg-background border border-border rounded-lg text-text-main text-sm focus:border-primary outline-none"
                        />
                    </div>
                    <button
                        onClick={runComparison}
                        disabled={loading}
                        className="flex items-center gap-2 px-5 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                        {loading ? <RefreshCw size={16} className="animate-spin" /> : <BarChart3 size={16} />}
                        {loading ? 'Running…' : 'Compare All Models'}
                    </button>
                </div>
                <p className="text-xs text-text-muted mt-3">
                    Uses default test circuit: R=1.2kΩ series → L=45mH series → C=15µF shunt
                </p>
            </div>

            {/* Results */}
            {compareResults.length > 0 && (
                <>
                    {/* Results table */}
                    <div className="bg-surface border border-border rounded-xl p-5">
                        <h3 className="font-semibold text-text-main mb-3 flex items-center gap-2">
                            <TrendingUp size={16} className="text-primary" />
                            Benchmark Results
                        </h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-text-muted border-b border-border">
                                        <th className="text-left py-2 pr-4">Model</th>
                                        <th className="text-right py-2 pr-4">Vout (V)</th>
                                        <th className="text-right py-2 pr-4">Error vs Physics (%)</th>
                                        <th className="text-right py-2 pr-4 flex items-center gap-1 justify-end">
                                            <Clock size={13} /> Latency (ms)
                                        </th>
                                        <th className="text-center py-2">Available</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {compareResults.map(r => (
                                        <tr key={r.model_name} className="border-b border-border/50 hover:bg-white/5">
                                            <td className="py-2 pr-4 font-medium" style={{ color: MODEL_COLORS[r.model_name] || '#94a3b8' }}>
                                                {MODEL_LABELS[r.model_name] || r.model_name}
                                            </td>
                                            <td className="py-2 pr-4 text-right font-mono">{(r.vout ?? 0).toFixed(6)}</td>
                                            <td className="py-2 pr-4 text-right font-mono">
                                                <span className={r.error_pct < 5 ? 'text-green-400' : r.error_pct < 15 ? 'text-yellow-500' : 'text-red-400'}>
                                                    {(r.error_pct ?? 0).toFixed(2)}%
                                                </span>
                                            </td>
                                            <td className="py-2 pr-4 text-right font-mono">{(r.latency_ms ?? 0).toFixed(3)}</td>
                                            <td className="py-2 text-center">
                                                {r.available ? (
                                                    <CheckCircle2 size={16} className="text-green-400 mx-auto" />
                                                ) : (
                                                    <XCircle size={16} className="text-yellow-500 mx-auto" />
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Bar chart: Vout by model */}
                    <div className="bg-surface border border-border rounded-xl p-5">
                        <h3 className="font-semibold text-text-main mb-4">Predicted Vout by Model</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                                    labelStyle={{ color: '#f1f5f9' }}
                                />
                                <Bar dataKey="vout" name="Vout (V)" fill="#6366f1" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Bar chart: latency */}
                    <div className="bg-surface border border-border rounded-xl p-5">
                        <h3 className="font-semibold text-text-main mb-4">Inference Latency (ms)</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                                    labelStyle={{ color: '#f1f5f9' }}
                                />
                                <Bar dataKey="latency_ms" name="Latency (ms)" fill="#22c55e" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </>
            )}
        </div>
    );
};

export default ModelComparisonDashboard;
