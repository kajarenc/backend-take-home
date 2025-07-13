#!/usr/bin/env python
from typing import Optional, List
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.responses import Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import time

from baseten_backend_take_home.repositories import metrics_repository

# Prometheus metrics
INVOCATION_COUNTER = Counter(
    "model_invocations_total",
    "Total number of model invocations",
    ["model_id", "status"],
)

INVOCATION_LATENCY = Histogram(
    "model_invocation_latency_seconds",
    "Latency of model invocations in seconds",
    ["model_id"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

ACTIVE_INVOCATIONS = Gauge(
    "model_active_invocations",
    "Number of active model invocations",
    ["model_id"],
)

TOTAL_INVOCATIONS = Gauge(
    "model_total_invocations",
    "Total number of invocations per model",
    ["model_id"],
)

SUCCESS_RATE = Gauge(
    "model_success_rate",
    "Success rate of model invocations as percentage",
    ["model_id"],
)


class MetricsCollector:
    """Handles Prometheus metrics collection and updates."""

    @staticmethod
    def increment_active_invocations(model_id: str):
        """Increment active invocations gauge for a model."""
        ACTIVE_INVOCATIONS.labels(model_id=model_id).inc()

    @staticmethod
    def decrement_active_invocations(model_id: str):
        """Decrement active invocations gauge for a model."""
        ACTIVE_INVOCATIONS.labels(model_id=model_id).dec()

    @staticmethod
    def record_invocation_metrics(
        model_id: str,
        success: bool,
        latency_seconds: float,
        latency_ms: int,
        error_log: str,
        input_size: int,
        output_size: int,
    ):
        """Record metrics for a completed invocation."""
        # Update Prometheus metrics
        status = "success" if success else "failure"
        INVOCATION_COUNTER.labels(model_id=model_id, status=status).inc()
        INVOCATION_LATENCY.labels(model_id=model_id).observe(latency_seconds)

        # Store detailed metrics in repository
        metrics_repository.record_invocation(
            model_id=model_id,
            success=success,
            latency_ms=latency_ms,
            error_log=error_log,
            input_size=input_size,
            output_size=output_size,
        )

        # Update gauges with latest stats
        stats = metrics_repository.get_model_stats(model_id)
        if model_id in stats:
            model_stats = stats[model_id]
            TOTAL_INVOCATIONS.labels(model_id=model_id).set(
                model_stats.total_invocations
            )
            SUCCESS_RATE.labels(model_id=model_id).set(
                model_stats.success_rate
            )


# Pydantic models for metrics endpoints
class InvocationHistoryResponse(BaseModel):
    history: List[dict]
    total_count: int
    offset: int
    limit: Optional[int]


class ModelStatsResponse(BaseModel):
    stats: dict


class MetricsEndpoints:
    """Handles metrics-related HTTP endpoints."""

    @staticmethod
    async def get_invocation_history(
        model_id: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: int = 0,
    ) -> InvocationHistoryResponse:
        """
        Get invocation history for all models or a specific model.

        Args:
            model_id: Optional model ID to filter by
            limit: Maximum number of records to return (default: 100)
            offset: Number of records to skip (default: 0)

        Returns:
            InvocationHistoryResponse with history records and pagination info
        """
        try:
            # Get invocation history from repository
            history = metrics_repository.get_invocation_history(
                model_id, limit, offset
            )

            # Convert to dict format
            history_dicts = [record.to_dict() for record in history]

            # Get total count for pagination
            total_count = metrics_repository.get_total_invocations()

            return InvocationHistoryResponse(
                history=history_dicts,
                total_count=total_count,
                offset=offset,
                limit=limit,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving invocation history: {str(e)}",
            )

    @staticmethod
    async def get_model_stats(
        model_id: Optional[str] = None,
    ) -> ModelStatsResponse:
        """
        Get success/failure statistics for all models or a specific model.

        Args:
            model_id: Optional model ID to get stats for specific model

        Returns:
            ModelStatsResponse with success/failure counts and rates
        """
        try:
            if model_id:
                # Get stats for specific model
                stats = metrics_repository.get_model_stats(model_id)
                if not stats:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No stats found for model: {model_id}",
                    )
                # Convert to dict format
                stats_dict = {
                    mid: stat.to_dict() for mid, stat in stats.items()
                }
            else:
                # Get stats for all models
                stats = metrics_repository.get_model_stats()
                stats_dict = {
                    mid: stat.to_dict() for mid, stat in stats.items()
                }

            return ModelStatsResponse(stats=stats_dict)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving model stats: {str(e)}",
            )

    @staticmethod
    async def get_prometheus_metrics():
        """
        Prometheus metrics endpoint for scraping.

        Returns:
            Response with Prometheus metrics in text format
        """
        try:
            metrics_data = generate_latest()
            return Response(
                content=metrics_data, media_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error generating metrics: {str(e)}"
            )
