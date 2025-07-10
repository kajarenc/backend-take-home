from typing import Dict, List, Optional
from .models import Organization, Model


class ModelRepository:
    """Repository for managing Model entities in memory"""

    def __init__(self):
        self._models: Dict[int, Model] = {}
        self._next_id = 1

    def create(self, name: str) -> Model:
        """Create a new model with auto-generated ID"""
        model = Model(id=self._next_id, name=name)
        self._models[self._next_id] = model
        self._next_id += 1
        return model

    def get_by_id(self, model_id: int) -> Optional[Model]:
        """Get a model by ID"""
        return self._models.get(model_id)

    def get_all(self) -> List[Model]:
        """Get all models"""
        return list(self._models.values())

    def update(self, model_id: int, name: str) -> Optional[Model]:
        """Update a model's name"""
        if model_id in self._models:
            self._models[model_id].name = name
            return self._models[model_id]
        return None

    def delete(self, model_id: int) -> bool:
        """Delete a model by ID"""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False


class OrganizationRepository:
    """Repository for managing Organization entities in memory"""

    def __init__(self):
        self._organizations: Dict[str, Organization] = {}
        self._next_id = 1

    def create(self, name: str) -> Organization:
        """Create a new organization with auto-generated ID"""
        org_id = str(self._next_id)
        organization = Organization(id=org_id, name=name)
        self._organizations[org_id] = organization
        self._next_id += 1
        return organization

    def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Get an organization by ID"""
        return self._organizations.get(org_id)

    def get_all(self) -> List[Organization]:
        """Get all organizations"""
        return list(self._organizations.values())

    def update(self, org_id: str, name: str) -> Optional[Organization]:
        """Update an organization's name"""
        if org_id in self._organizations:
            self._organizations[org_id].name = name
            return self._organizations[org_id]
        return None

    def delete(self, org_id: str) -> bool:
        """Delete an organization by ID"""
        if org_id in self._organizations:
            del self._organizations[org_id]
            return True
        return False

    def add_model_to_organization(self, org_id: str, model: Model) -> bool:
        """Add a model to an organization"""
        if org_id in self._organizations:
            self._organizations[org_id].add_model(model)
            return True
        return False

    def remove_model_from_organization(
        self, org_id: str, model_id: int
    ) -> bool:
        """Remove a model from an organization"""
        if org_id in self._organizations:
            return self._organizations[org_id].remove_model(model_id)
        return False


# Global repository instances
model_repository = ModelRepository()
organization_repository = OrganizationRepository()

# Initialize with some sample data
sample_org1 = organization_repository.create("Baseten")
sample_org2 = organization_repository.create("Strawberry")

sample_model1 = model_repository.create("GPT-3.5")
sample_model2 = model_repository.create("BERT")
sample_model3 = model_repository.create("ResNet")

# Add some models to organizations
organization_repository.add_model_to_organization(
    sample_org1.id, sample_model1
)
organization_repository.add_model_to_organization(
    sample_org1.id, sample_model2
)
organization_repository.add_model_to_organization(
    sample_org2.id, sample_model3
)
