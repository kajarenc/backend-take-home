from typing import Dict, List, Optional
from baseten_backend_take_home.models import Organization, Model
from datetime import datetime
from baseten_backend_take_home.models import InvocationRecord, ModelStats


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


class MetricsRepository:
    """Repository for managing invocation metrics and history"""

    def __init__(self):
        self._invocation_records: Dict[int, InvocationRecord] = {}
        self._model_stats: Dict[str, ModelStats] = {}
        self._next_record_id = 1

    def record_invocation(
        self,
        model_id: str,
        success: bool,
        latency_ms: int,
        error_log: str = "",
        input_size: int = 0,
        output_size: int = 0,
    ) -> InvocationRecord:
        """Record a new invocation and update model stats"""
        # Create invocation record
        record = InvocationRecord(
            id=self._next_record_id,
            model_id=model_id,
            timestamp=datetime.now(),
            success=success,
            latency_ms=latency_ms,
            error_log=error_log,
            input_size=input_size,
            output_size=output_size,
        )

        self._invocation_records[self._next_record_id] = record
        self._next_record_id += 1

        # Update model stats
        self._update_model_stats(record)

        return record

    def _update_model_stats(self, record: InvocationRecord) -> None:
        """Update statistics for a model based on a new invocation"""
        model_id = record.model_id

        if model_id not in self._model_stats:
            # Initialize stats for new model
            self._model_stats[model_id] = ModelStats(
                model_id=model_id,
                total_invocations=0,
                successful_invocations=0,
                failed_invocations=0,
                average_latency_ms=0.0,
                total_latency_ms=0,
                min_latency_ms=999999,  # Large initial value
                max_latency_ms=0,
                last_invocation=None,
            )

        stats = self._model_stats[model_id]

        # Update counters
        stats.total_invocations += 1
        if record.success:
            stats.successful_invocations += 1
        else:
            stats.failed_invocations += 1

        # Update latency stats
        stats.total_latency_ms += record.latency_ms
        stats.average_latency_ms = (
            stats.total_latency_ms / stats.total_invocations
        )
        stats.min_latency_ms = min(stats.min_latency_ms, record.latency_ms)
        stats.max_latency_ms = max(stats.max_latency_ms, record.latency_ms)
        stats.last_invocation = record.timestamp

    def get_invocation_history(
        self,
        model_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[InvocationRecord]:
        """Get invocation history, optionally filtered by model_id"""
        records = list(self._invocation_records.values())

        # Filter by model_id if provided
        if model_id:
            records = [r for r in records if r.model_id == model_id]

        # Sort by timestamp descending (newest first)
        records.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        start = offset
        end = start + limit if limit else len(records)

        return records[start:end]

    def get_model_stats(
        self, model_id: Optional[str] = None
    ) -> Dict[str, ModelStats]:
        """Get statistics for all models or a specific model"""
        if model_id:
            if model_id in self._model_stats:
                return {model_id: self._model_stats[model_id]}
            return {}
        return self._model_stats.copy()

    def get_total_invocations(self) -> int:
        """Get total number of invocations across all models"""
        return len(self._invocation_records)

    def get_success_failure_counts(self) -> Dict[str, Dict[str, int]]:
        """Get success/failure counts for all models"""
        result = {}
        for model_id, stats in self._model_stats.items():
            result[model_id] = {
                "successful": stats.successful_invocations,
                "failed": stats.failed_invocations,
                "total": stats.total_invocations,
                "success_rate": stats.success_rate,
                "failure_rate": stats.failure_rate,
            }
        return result


# Global repository instances
model_repository = ModelRepository()
organization_repository = OrganizationRepository()
metrics_repository = MetricsRepository()

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
