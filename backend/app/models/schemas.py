from pydantic import BaseModel


class CircuitParams(BaseModel):
    R: float
    L: float
    C: float
    frequency: float = 1000.0
    vin: float = 1.0


class TopologicalComponent(BaseModel):
    tag: int   # 1: Series, 2: Shunt, 0: Terminate
    type: str  # 'R', 'L', 'C'
    value: float


class TopologicalCircuit(BaseModel):
    stages: list[TopologicalComponent]
    frequency: float = 1000.0
    vin: float = 1.0


class BenchmarkResult(BaseModel):
    solver_vout: float
    solver_time_ms: float
    ai_vout: float
    ai_time_ms: float
    error_abs: float
    error_percent: float
    speed_factor: float
    iin_ma: float = 0.0
    efficiency: float = 0.0
    rise_time_ms: float = 0.0
    settling_time_ms: float = 0.0
    overshoot_pct: float = 0.0
    ai_source: str = "local"
    is_ood: bool = False
    hardware: str = "Host-CPU"


class RemoteConfigRequest(BaseModel):
    url: str


class ModelInfo(BaseModel):
    name: str
    available: bool
    description: str


class ModelCompareRequest(BaseModel):
    stages: list[TopologicalComponent]
    frequency: float = 1000.0
    vin: float = 1.0


class ModelCompareResult(BaseModel):
    model_name: str
    vout: float
    latency_ms: float
    source: str
