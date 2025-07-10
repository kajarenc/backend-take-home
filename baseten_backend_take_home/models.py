from dataclasses import dataclass
from typing import List, Optional


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
