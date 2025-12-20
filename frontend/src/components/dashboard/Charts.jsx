import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export const TransientChart = ({ physicsVout, aiVout, frequency }) => {
    // Safety checks to prevent crashes
    const safeFreq = Number.isFinite(frequency) && frequency > 0 ? frequency : 1000;
    const safePhysics = Number.isFinite(physicsVout) ? physicsVout : 0;
    const safeAi = Number.isFinite(aiVout) ? aiVout : 0;

    // Generate sine waves based on magnitude
    const data = [];
    const points = 50;
    const period = 1 / safeFreq;
    // Show 2 cycles
    const duration = period * 2;

    for (let i = 0; i <= points; i++) {
        const t = (i / points) * duration;
        data.push({
            time: (t * 1000).toFixed(2), // ms
            physics: safePhysics * Math.sin(2 * Math.PI * safeFreq * t),
            ai: safeAi * Math.sin(2 * Math.PI * safeFreq * t)
        });
    }

    return (
        <div className="h-[300px] w-full bg-surface/50 border border-border rounded-xl p-4">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-semibold text-white">Transient Response <span className="text-text-muted font-normal text-xs ml-2">(Simulated from Magnitude)</span></h3>
                <div className="flex gap-4 text-xs">
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-0.5 bg-text-muted"></span>
                        <span className="text-text-muted">Physics</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-0.5 bg-primary border border-primary border-dashed"></span>
                        <span className="text-primary">AI Prediction</span>
                    </div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis
                        dataKey="time"
                        stroke="#9ca3af"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(val) => `${val}ms`}
                    />
                    <YAxis
                        stroke="#9ca3af"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(val) => `${val}V`}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }}
                        itemStyle={{ padding: 0 }}
                    />
                    <Line
                        type="monotone"
                        dataKey="physics"
                        stroke="#9ca3af"
                        strokeWidth={2}
                        dot={false}
                    />
                    <Line
                        type="monotone"
                        dataKey="ai"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        strokeDasharray="4 4"
                        dot={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export const ErrorSweepChart = () => {
    // Mock data for the sweep visualization as per design
    const data = [
        { freq: 10, error: 0.5 },
        { freq: 50, error: 0.6 },
        { freq: 100, error: 0.8 },
        { freq: 200, error: 1.2 },
        { freq: 450, error: 2.1, active: true },
        { freq: 800, error: 2.3 },
        { freq: 1000, error: 2.8 },
    ];

    return (
        <div className="h-[300px] w-full bg-surface/50 border border-border rounded-xl p-4">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-semibold text-white">Error Magnitude vs. Frequency</h3>
                <div className="p-1 rounded bg-white/5 hover:bg-white/10 cursor-pointer transition-colors">
                    <span className="text-xs text-text-muted">Expand</span>
                </div>
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                    <XAxis
                        dataKey="freq"
                        stroke="#9ca3af"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(val) => `${val}Hz`}
                    />
                    <YAxis
                        stroke="#9ca3af"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(val) => `${val}%`}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }}
                    />
                    <Line
                        type="monotone"
                        dataKey="error"
                        stroke="#3b82f6"
                        strokeWidth={1}
                        dot={{ r: 3, fill: "#3b82f6", strokeWidth: 0 }}
                    />
                    {/* Highlighted point */}
                    <ReferenceLine x={450} stroke="#ef4444" strokeDasharray="3 3" />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}
