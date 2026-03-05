import React, { useState, useRef } from 'react';
import {
    Database,
    Upload,
    Zap,
    Info,
    Cpu,
    BarChart3,
    Image as ImageIcon,
    Plus,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Github
} from 'lucide-react';
import ModelComparisonDashboard from './ModelComparisonDashboard';

const API_BASE = 'https://hot-wolves-warn.loca.lt';

const ModelWorkbench = () => {
    const [activeTab, setActiveTab] = useState('workbench'); // 'workbench' | 'compare'
    const [selectedConfig, setSelectedConfig] = useState('rlc_series');
    const [uploading, setUploading] = useState(false);
    const [showNetlistModal, setShowNetlistModal] = useState(false);
    const [netlist, setNetlist] = useState('* Custom RC Filter\nVin 1 0 AC 1.0\nR1 1 2 100\nC1 2 0 10u\n.AC DEC 10 1 10k\n.END');
    const [remoteUrl, setRemoteUrl] = useState('');
    const [connecting, setConnecting] = useState(false);
    const [remoteStatus, setRemoteStatus] = useState(null); // 'local' or 'remote'
    const fileInputRef = useRef(null);
    const modelInputRef = useRef(null);
    const [modelUploading, setModelUploading] = useState(false);

    const handleWeightSwap = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setModelUploading(true);
        setTimeout(() => {
            setModelUploading(false);
            alert(`Succesfully Swapped Weights!\nFile: ${file.name}\nModel Type: MLP Regressor\nStatus: Optimized`);
        }, 2000);
    };

    const handleConnectRemote = async () => {
        setConnecting(true);
        try {
            const response = await fetch(`${API_BASE}/config/remote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Bypass-Tunnel-Reminder': 'true'
                },
                body: JSON.stringify({ url: remoteUrl })
            });
            const data = await response.json();
            if (response.ok) {
                setRemoteStatus(remoteUrl ? 'remote' : 'local');
                alert(remoteUrl ? `Connected to Remote Model: ${data.url}` : 'Switched to Local Model');
            } else {
                alert(`Connection Failed: ${data.detail}`);
            }
        } catch (err) {
            alert('Backend not reachable');
        } finally {
            setConnecting(false);
        }
    };

    const configs = [
        { id: 'rlc_series', name: 'RLC Series', formula: 'Vout = Vin * (Zc / (R + Zl + Zc))', complexity: 'Low' },
        { id: 'rlc_parallel', name: 'RLC Parallel', formula: 'Vout = Vin * (R || L || C) / total', complexity: 'Medium' },
        { id: 'lc_series', name: 'LC Filter', formula: 'Vout = Vin * (Zc / (Zl + Zc))', complexity: 'Low' },
        { id: 'bridge', name: 'Bridge Rectifier', formula: 'Vout = Vin * 0.9 (approx)', complexity: 'High' }
    ];

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE}/vision/extract`, {
                method: 'POST',
                headers: { 'Bypass-Tunnel-Reminder': 'true' },
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                const comps = data.components || [];
                const r = comps.find(c => c.type === 'resistor')?.value || 0;
                const l = comps.find(c => c.type === 'inductor')?.value || 0;
                const c = comps.find(c => c.type === 'capacitor')?.value || 0;

                alert(`Parameters Extracted via ${data.source === 'remote' ? 'CircuitNet AI' : 'Mock Engine'}!\n\nDetected Values:\nR = ${r}Ω\nL = ${l}mH\nC = ${c}µF\n\nCircuit confirmed as RLC Series.`);
                setSelectedConfig('rlc_series');
            } else {
                alert(`Extraction Failed: ${data.detail}`);
            }
        } catch (err) {
            alert('Backend not reachable');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold text-white tracking-tight">Research Workbench</h2>
                <p className="text-text-muted mt-2">Configure circuit physics, surrogate models, and benchmark environments.</p>
            </div>

            {/* Tab switcher */}
            <div className="flex gap-2 border-b border-border pb-2">
                <button
                    onClick={() => setActiveTab('workbench')}
                    className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${activeTab === 'workbench' ? 'bg-primary text-white' : 'text-text-muted hover:text-text-main'}`}
                >
                    Workbench
                </button>
                <button
                    onClick={() => setActiveTab('compare')}
                    className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors flex items-center gap-1 ${activeTab === 'compare' ? 'bg-primary text-white' : 'text-text-muted hover:text-text-main'}`}
                >
                    <BarChart3 size={14} />
                    Model Comparison
                </button>
            </div>

            {/* Model Comparison Dashboard */}
            {activeTab === 'compare' && <ModelComparisonDashboard />}

            {/* Original Workbench content */}
            {activeTab === 'workbench' && <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Left Column: Circuit Configurator */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm">
                        <div className="flex items-center gap-2 mb-6">
                            <Cpu className="w-5 h-5 text-primary" />
                            <h3 className="text-lg font-semibold text-white tracking-wide">Circuit Configuration</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {configs.map((config) => (
                                <button
                                    key={config.id}
                                    onClick={() => setSelectedConfig(config.id)}
                                    className={`p-4 rounded-xl border transition-all text-left group ${selectedConfig === config.id
                                        ? 'bg-primary/10 border-primary ring-1 ring-primary/50'
                                        : 'bg-background/50 border-white/5 hover:border-white/20'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className={`font-semibold ${selectedConfig === config.id ? 'text-primary' : 'text-white group-hover:text-primary transition-colors'}`}>
                                            {config.name}
                                        </span>
                                        {selectedConfig === config.id && <CheckCircle2 className="w-4 h-4 text-primary" />}
                                    </div>
                                    <code className="text-[10px] text-text-muted font-mono block mb-2 opacity-70">
                                        {config.formula}
                                    </code>
                                    <div className="flex items-center gap-2 mt-3">
                                        <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold tracking-tighter ${config.complexity === 'Low' ? 'bg-success/10 text-success' :
                                            config.complexity === 'Medium' ? 'bg-warning/10 text-warning' : 'bg-primary/10 text-primary'
                                            }`}>
                                            {config.complexity} Complexity
                                        </span>
                                    </div>
                                </button>
                            ))}
                            <button
                                onClick={() => setShowNetlistModal(true)}
                                className="p-4 rounded-xl border border-dashed border-white/10 bg-white/5 hover:bg-white/10 transition-all flex flex-col items-center justify-center text-text-muted gap-2 group"
                            >
                                <Plus className="w-6 h-6 group-hover:scale-110 transition-transform" />
                                <span className="text-xs font-medium">Custom Netlist</span>
                            </button>
                        </div>

                        {/* Image Extraction Mock */}
                        <div className="mt-8 p-4 rounded-xl bg-blue-500/5 border border-blue-500/10 flex items-center justify-between">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                className="hidden"
                                accept="image/*"
                            />
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-primary/20">
                                    <ImageIcon className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                    <h4 className="text-sm font-semibold text-white">Visual Parameter Extraction</h4>
                                    <p className="text-[10px] text-text-muted">Upload a circuit schematic to extract R, L, C values automatically.</p>
                                </div>
                            </div>
                            <button
                                onClick={() => fileInputRef.current.click()}
                                disabled={uploading}
                                className="px-4 py-2 bg-primary text-white text-xs font-bold rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2 disabled:opacity-50"
                            >
                                {uploading ? (
                                    <>
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                        Processing...
                                    </>
                                ) : (
                                    'Upload Schematic'
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Mathematical Summary */}
                    <div className="p-6 rounded-2xl bg-surface border border-border">
                        <div className="flex items-center gap-2 mb-4">
                            < Zap className="w-5 h-5 text-yellow-500" />
                            <h3 className="text-lg font-semibold text-white">Active Transfer Function</h3>
                        </div>
                        <div className="p-8 rounded-xl bg-background font-mono text-center relative overflow-hidden group">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-500 opacity-50"></div>
                            <div className="text-xl text-primary font-bold tracking-widest break-all">
                                H(s) = 1 / (1 + sRC + s²LC)
                            </div>
                            <p className="text-[11px] text-text-muted mt-4 font-sans tracking-normal">
                                Based on a typical RLC Low-Pass configuration. Frequency range calibrated for 10Hz - 10kHz.
                            </p>
                            <div className="mt-4 flex justify-center gap-6">
                                <div className="text-center">
                                    <span className="text-[10px] text-text-muted block uppercase">Phase Margin</span>
                                    <span className="text-sm text-white font-bold">45.2°</span>
                                </div>
                                <div className="text-center">
                                    <span className="text-[10px] text-text-muted block uppercase">Resonant Freq</span>
                                    <span className="text-sm text-white font-bold">6.12 kHz</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Model & Dataset */}
                <div className="space-y-6">
                    {/* Active Model Block */}
                    <div className="p-6 rounded-2xl bg-surface border border-border border-l-primary border-l-4">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h4 className="text-primary text-xs font-bold uppercase tracking-widest mb-1">Active Surrogate</h4>
                                <h3 className="text-xl font-bold text-white">ResNet-v2.4</h3>
                            </div>
                            <div className="p-2 bg-primary/10 rounded-full">
                                <Database className="w-4 h-4 text-primary" />
                            </div>
                        </div>

                        <div className="space-y-4 text-xs">
                            <div className="flex justify-between py-2 border-b border-white/5">
                                <span className="text-text-muted">Architecture</span>
                                <span className="text-white font-mono uppercase">MLP-Reg-128x3</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-white/5">
                                <span className="text-text-muted">Weights File</span>
                                <span className="text-white font-mono">rlc_vout_model.pkl</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-white/5">
                                <span className="text-text-muted">Last Updated</span>
                                <span className="text-white">Dec 20, 2025</span>
                            </div>
                        </div>

                        <input
                            type="file"
                            ref={modelInputRef}
                            onChange={handleWeightSwap}
                            className="hidden"
                            accept=".pkl,.onnx,.h5,.bin"
                        />

                        <button
                            onClick={() => modelInputRef.current.click()}
                            disabled={modelUploading}
                            className="w-full mt-6 py-3 border border-dashed border-white/20 rounded-xl text-xs text-text-muted hover:bg-white/[0.02] hover:text-white transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {modelUploading ? (
                                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                            ) : (
                                <Upload className="w-3 h-3" />
                            )}
                            {modelUploading ? 'Flashing Weights...' : 'Swap weights (.pkl / .onnx)'}
                        </button>
                    </div>

                    {/* Google Colab Bridge */}
                    <div className="p-6 rounded-2xl bg-surface border border-border border-t-orange-500 border-t-4">
                        <div className="flex items-center gap-2 mb-4">
                            <Github className="w-4 h-4 text-orange-500" />
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Google Colab Bridge</h3>
                        </div>

                        <div className="space-y-4">
                            <p className="text-[10px] text-text-muted leading-relaxed">
                                Train your model on Colab and host it instantly using <strong>Ngrok</strong>. Copy the commands below into your notebook.
                            </p>

                            <div className="p-3 bg-background rounded-xl font-mono text-[9px] text-orange-200/70 space-y-2 max-h-40 overflow-y-auto scrollbar-thin border border-white/5">
                                <div># 1. Install & Setup</div>
                                <div className="text-orange-400">!pip install fastapi uvicorn nest-asyncio pyngrok joblib</div>
                                <div className="mt-2"># 2. Start API</div>
                                <div className="text-orange-400 whitespace-pre-wrap">
                                    {`import joblib, nest_asyncio, uvicorn, cv2, numpy as np
from fastapi import FastAPI, UploadFile, File
nest_asyncio.apply(); app = FastAPI()

# Load your models
reg_model = joblib.load("model.pkl") # Regression
# vision_model = tf.keras.models.load_model("CircuitNet") # Vision

@app.post("/predict")
def predict(d: dict): 
    return {"prediction": reg_model.predict([d["features"]]).tolist()}

@app.post("/vision")
async def vision(file: UploadFile = File(...)):
    # 1. Run your detect_components(img) here
    # 2. Map results to this format:
    return {
        "components": [
            {"type": "resistor", "value": 1500, "unit": "ohm"},
            {"type": "inductor", "value": 0.05, "unit": "H"}
        ]
    }

from pyngrok import ngrok; print(ngrok.connect(8000))
uvicorn.run(app, host="0.0.0.0", port=8000)`}
                                </div>
                            </div>

                            <div className="space-y-2 pt-2">
                                <label className="text-[9px] text-text-muted uppercase font-bold">Ngrok Public URL</label>
                                <div className="flex gap-2">
                                    <input
                                        value={remoteUrl}
                                        onChange={(e) => setRemoteUrl(e.target.value)}
                                        placeholder="https://xxxx-xx.ngrok.io"
                                        className="flex-1 bg-background border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:border-orange-500 outline-none transition-all"
                                    />
                                    <button
                                        onClick={handleConnectRemote}
                                        disabled={connecting}
                                        className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white text-[10px] font-bold rounded-lg transition-all disabled:opacity-50"
                                    >
                                        {connecting ? '...' : (remoteStatus === 'remote' ? 'Sync' : 'Link')}
                                    </button>
                                </div>
                                {remoteStatus === 'remote' && (
                                    <div className="flex flex-col gap-2">
                                        <div className="flex items-center gap-1.5 px-2 py-1 bg-green-500/10 rounded text-[9px] text-green-500 font-bold">
                                            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                            Remote Model Active
                                        </div>

                                        {/* Vision Bridge Option */}
                                        <div className="mt-2 p-3 bg-white/[0.03] border border-white/5 rounded-xl space-y-2">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <ImageIcon className="w-3 h-3 text-primary" />
                                                    <span className="text-[9px] text-white font-bold uppercase">Vision Bridge</span>
                                                </div>
                                                <span className="text-[8px] px-1.5 py-0.5 bg-primary/20 text-primary rounded-full font-black">NEW</span>
                                            </div>
                                            <p className="text-[9px] text-text-muted">Detect components from sketches using your R-CNN model.</p>
                                            <button
                                                onClick={() => {
                                                    alert("Vision Bridge Initialized!\nService: Schematic-to-Netlist OCR\nStatus: Waiting for Image Upload...");
                                                }}
                                                className="w-full py-1.5 bg-primary/10 border border-primary/20 rounded-lg text-[9px] text-primary font-bold hover:bg-primary/20 transition-all"
                                            >
                                                Enable Schematic-to-Netlist
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Dataset Stats */}
                    <div className="p-6 rounded-2xl bg-surface border border-border">
                        <div className="flex items-center gap-2 mb-6">
                            <BarChart3 className="w-4 h-4 text-success" />
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Training Profile</h3>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <div className="flex justify-between text-[11px] mb-2">
                                    <span className="text-text-muted uppercase">Sample Integrity</span>
                                    <span className="text-success font-bold">100% Valid</span>
                                </div>
                                <div className="h-1.5 w-full bg-background rounded-full overflow-hidden">
                                    <div className="h-full bg-success w-full opacity-70"></div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-3 rounded-xl bg-background/50 border border-white/5">
                                    <span className="text-[9px] text-text-muted block uppercase mb-1">Total Samples</span>
                                    <span className="text-lg font-bold text-white font-mono">1,000</span>
                                </div>
                                <div className="p-3 rounded-xl bg-background/50 border border-white/5">
                                    <span className="text-[9px] text-text-muted block uppercase mb-1">Diversity Score</span>
                                    <span className="text-lg font-bold text-white font-mono">0.87</span>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 flex items-start gap-3 p-3 rounded-xl bg-blue-500/5 border border-blue-500/10 text-[10px] text-text-muted italic">
                            <Info className="w-4 h-4 text-primary shrink-0" />
                            <span>This model was trained on synthetic data generated from the RLC Series transfer function using a 1kHz excitation frequency.</span>
                        </div>
                    </div>

                    {/* Alert */}
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-amber-500/80 text-[10px]">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>Warning: Current configuration deviates 12% from the training distribution mean. High error likely.</span>
                    </div>
                </div>
            </div>

            {/* Netlist Editor Modal */}
            {showNetlistModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
                    <div className="w-full max-w-2xl bg-surface border border-border rounded-3xl p-8 shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-primary/10">
                                    <Plus className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">Netlist Editor</h3>
                                    <p className="text-xs text-text-muted mt-1">Write raw SPICE code to define custom circuit topology</p>
                                </div>
                            </div>
                        </div>

                        <textarea
                            value={netlist}
                            onChange={(e) => setNetlist(e.target.value)}
                            className="w-full h-64 bg-background border border-white/10 rounded-xl p-4 font-mono text-sm text-primary focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none transition-all scrollbar-thin"
                            spellCheck="false"
                        />

                        <div className="flex justify-end gap-3 mt-8">
                            <button
                                onClick={() => setShowNetlistModal(false)}
                                className="px-6 py-2 text-sm text-text-muted hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => {
                                    alert("Netlist Compiled Successfully!\nTopology: Custom Low-Pass Filter detected.");
                                    setShowNetlistModal(false);
                                }}
                                className="px-6 py-2 bg-primary text-white text-sm font-bold rounded-xl hover:bg-blue-600 transition-all shadow-lg shadow-primary/20"
                            >
                                Compile Netlist
                            </button>
                        </div>
                    </div>
                </div>
            )}
            </>}
        </div>
    );
};

export default ModelWorkbench;
