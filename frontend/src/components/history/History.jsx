import React from 'react';
import { History as HistoryIcon, Trash2, ExternalLink, Activity, Sparkles, Clock } from 'lucide-react';

const History = ({ history, onClearHistory }) => {
    if (!history || history.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-20 border border-dashed border-white/10 rounded-2xl bg-white/5 mx-auto">
                <HistoryIcon className="w-12 h-12 text-text-muted mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-white">No Simulation History</h3>
                <p className="text-text-muted max-w-md text-center mt-2">
                    Your past simulation runs will appear here once you run a comparison in the Simulator tab.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                        Simulation History
                    </h2>
                    <p className="text-text-muted text-sm mt-1">Review and compare past benchmark results</p>
                </div>
                <button
                    onClick={onClearHistory}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-warning hover:bg-warning/10 rounded-lg transition-colors border border-warning/20"
                >
                    <Trash2 className="w-4 h-4" />
                    Clear History
                </button>
            </div>

            <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-white/5 border-b border-white/5">
                            <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Parameters</th>
                            <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Metrics (V, I, η)</th>
                            <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Transient (tr, Mp)</th>
                            <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Error %</th>
                            <th className="p-4 text-xs font-semibold text-text-muted uppercase tracking-wider">Speedup</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {[...history].reverse().map((run, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors group">
                                <td className="p-4">
                                    <div className="text-[10px] text-white font-mono bg-white/5 p-1 rounded">
                                        {new Date(run.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </td>
                                <td className="p-4">
                                    {run.params.encoding ? (
                                        <div className="text-[9px] font-mono text-primary max-w-[120px] truncate" title={run.params.encoding}>
                                            {run.params.encoding}
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-2 gap-x-3 text-[10px] font-mono text-text-muted">
                                            <span>R:{run.params.R}Ω</span>
                                            <span>L:{run.params.L}H</span>
                                            <span>C:{(run.params.C * 1e6).toFixed(1)}µ</span>
                                            <span>F:{run.params.frequency}Hz</span>
                                        </div>
                                    )}
                                </td>
                                <td className="p-4">
                                    <div className="space-y-1">
                                        <div className="text-xs font-bold text-white">{(run.results.solver_vout || 0).toFixed(2)}V / {(run.results.iin_ma || 0).toFixed(1)}mA</div>
                                        <div className="text-[9px] text-success font-bold uppercase">η: {((run.results.efficiency || 0) * 100).toFixed(1)}%</div>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className="space-y-1">
                                        <div className="text-xs text-blue-400 font-mono">tr: {(run.results.rise_time_ms || 0).toFixed(2)}ms</div>
                                        <div className="text-[9px] text-orange-400 font-bold uppercase">Mp: {(run.results.overshoot_pct || 0).toFixed(1)}%</div>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className={`text-sm font-bold ${run.results.error_percent < 1.0 ? 'text-success' : 'text-warning'}`}>
                                        {run.results.error_percent.toFixed(2)}%
                                    </div>
                                    <div className="text-[10px] text-text-muted mt-1">
                                        Δ {run.results.error_abs.toFixed(5)}V
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className="text-sm text-accent font-bold">
                                        {(run.results.speed_factor || run.results.speedup_factor || 0).toFixed(1)}x
                                    </div>
                                    <div className="text-[10px] text-text-muted mt-1 uppercase tracking-tighter">Faster</div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default History;
