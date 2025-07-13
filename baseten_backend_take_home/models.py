from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Model:
    id: int
    name: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


@dataclass
class Organization:
    id: str
    name: str
    models: List[Model]

    def __init__(
        self, id: str, name: str, models: Optional[List[Model]] = None
    ):
        self.id = id
        self.name = name
        self.models = models or []

    def add_model(self, model: Model) -> None:
        """Add a model to this organization if it doesn't already exist"""
        if model not in self.models:
            self.models.append(model)

    def remove_model(self, model_id: int) -> bool:
        """Remove a model from this organization by ID.
        Returns True if removed, False if not found
        """
        for i, model in enumerate(self.models):
            if model.id == model_id:
                self.models.pop(i)
                return True
        return False

    def get_model(self, model_id: int) -> Optional[Model]:
        """Get a model by ID from this organization"""
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "models": [model.to_dict() for model in self.models],
        }


@dataclass
class InvocationRecord:
    """Record of a single model invocation"""

    id: int
    model_id: str
    timestamp: datetime
    success: bool
    latency_ms: int
    error_log: str
    input_size: int  # Size of the input data
    output_size: int  # Size of the output data

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model_id": self.model_id,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "latency_ms": self.latency_ms,
            "error_log": self.error_log,
            "input_size": self.input_size,
            "output_size": self.output_size,
        }


@dataclass
class ModelStats:
    """Statistics for a specific model"""

    model_id: str
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    average_latency_ms: float
    total_latency_ms: int
    min_latency_ms: int
    max_latency_ms: int
    last_invocation: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_invocations == 0:
            return 0.0
        return (self.successful_invocations / self.total_invocations) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage"""
        return 100.0 - self.success_rate

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "total_invocations": self.total_invocations,
            "successful_invocations": self.successful_invocations,
            "failed_invocations": self.failed_invocations,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "average_latency_ms": self.average_latency_ms,
            "total_latency_ms": self.total_latency_ms,
            "min_latency_ms": self.min_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "last_invocation": self.last_invocation.isoformat()
            if self.last_invocation
            else None,
        }
