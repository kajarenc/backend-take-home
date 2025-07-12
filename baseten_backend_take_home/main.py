#!/usr/bin/env python
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

import aiohttp
import strawberry
import json
import os

from baseten_backend_take_home.repositories import organization_repository, model_repository, metrics_repository

# Prometheus metrics
INVOCATION_COUNTER = Counter(
    'model_invocations_total',
    'Total number of model invocations',
    ['model_id', 'status']
)

INVOCATION_LATENCY = Histogram(
    'model_invocation_latency_seconds',
    'Latency of model invocations in seconds',
    ['model_id'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

ACTIVE_INVOCATIONS = Gauge(
    'model_active_invocations',
    'Number of active model invocations',
    ['model_id']
)

TOTAL_INVOCATIONS = Gauge(
    'model_total_invocations',
    'Total number of invocations per model',
    ['model_id']
)

SUCCESS_RATE = Gauge(
    'model_success_rate',
    'Success rate of model invocations as percentage',
    ['model_id']
)


# Unimplemented is an util for all the unimplemented stuff
# left here
class Unimplemented(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("Unimplemented!")


#################
# API Client
# This is just a basic boilerplate to setup
#################
class Endpoint(BaseModel):
    url: str
    authorization: Optional[str] = Field(default_factory=lambda: None)

    async def exec(self, json_str: str) -> aiohttp.ClientResponse:
        headers = {
            "content-type": "application/json",
        }
        if self.authorization is not None:
            headers["authorization"] = self.authorization

        async with aiohttp.ClientSession() as session:
            return await session.post(
                url=self.url,
                data=json_str,
                headers=headers,
            )


DEFAULT_ENDPOINT = Endpoint(
    url="https://app.staging.baseten.co/applications/Vqmogn0/worklets/VBnodk0/invoke",  # noqa
    authorization="Api-Key IR5hVxK1.FlYV3hmIazD7FGvXPacQnN38wgw7CSSE",
)

MOCK_ENDPOINT = Endpoint(url=f"{os.getenv('MOCK_SERVER_URL', 'http://localhost:8001')}/invoke")


#################
# GRAPHQL API
# This is just a basic boilerplate to setup a graphql api backed by strawberry
# see: https://strawberry.rocks/docs for docs
#################
@strawberry.type
class Model:
    id: int
    name: str


@strawberry.type
class Organization:
    id: str
    name: str
    models: List[Model]


@strawberry.type
class Query:
    @strawberry.field
    async def organizations(self) -> List[Organization]:
        orgs = organization_repository.get_all()
        return [
            Organization(
                id=org.id,
                name=org.name,
                models=[
                    Model(id=model.id, name=model.name) for model in org.models
                ],
            )
            for org in orgs
        ]

    @strawberry.field
    async def organization(self, id: str) -> Optional[Organization]:
        org = organization_repository.get_by_id(id)
        if org:
            return Organization(
                id=org.id,
                name=org.name,
                models=[
                    Model(id=model.id, name=model.name) for model in org.models
                ],
            )
        return None

    @strawberry.field
    async def models(self) -> List[Model]:
        models = model_repository.get_all()
        return [Model(id=model.id, name=model.name) for model in models]

    @strawberry.field
    async def model(self, id: int) -> Optional[Model]:
        model = model_repository.get_by_id(id)
        if model:
            return Model(id=model.id, name=model.name)
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_organization(self, name: str) -> Organization:
        org = organization_repository.create(name)
        return Organization(
            id=org.id,
            name=org.name,
            models=[
                Model(id=model.id, name=model.name) for model in org.models
            ],
        )

    @strawberry.mutation
    async def create_model(self, name: str) -> Model:
        model = model_repository.create(name)
        return Model(id=model.id, name=model.name)

    @strawberry.mutation
    async def add_model_to_organization(
        self, organization_id: str, model_id: int
    ) -> bool:
        model = model_repository.get_by_id(model_id)
        if model:
            return organization_repository.add_model_to_organization(
                organization_id, model
            )
        return False

    @strawberry.mutation
    async def remove_model_from_organization(
        self, organization_id: str, model_id: int
    ) -> bool:
        return organization_repository.remove_model_from_organization(
            organization_id, model_id
        )


SCHEMA = strawberry.Schema(Query, Mutation)


#################
# HTTP API
# This is just a basic boilerplate to setup a HTTP API using FastAPI
# see: https://fastapi.tiangolo.com/ for docs
#################


# Pydantic models for the invoke endpoint
class WorkletInput(BaseModel):
    model_id: str
    input: List[int]


class InvokeRequest(BaseModel):
    worklet_input: WorkletInput


class InvokeResponse(BaseModel):
    worklet_output: List[int]
    success: bool
    latency_ms: int
    error_log: str


app = FastAPI()


@app.get("/healtz", response_class=HTMLResponse)
def health_check():
    return """
        Welcome to baseten_take_home invoker,
        go to <a href="/graphql">/graphql</a> for the API doc
    """


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_model(request: InvokeRequest) -> InvokeResponse:
    model_id = request.worklet_input.model_id
    start_time = time.time()
    
    # Increment active invocations gauge
    ACTIVE_INVOCATIONS.labels(model_id=model_id).inc()
    
    try:
        json_str = json.dumps(request.model_dump())
        response = await MOCK_ENDPOINT.exec(json_str)
        response_data = await response.json()
        invoke_response = InvokeResponse(**response_data)
        
        # Calculate metrics
        end_time = time.time()
        latency_seconds = end_time - start_time
        latency_ms = int(latency_seconds * 1000)
        
        # Update Prometheus metrics
        status = "success" if invoke_response.success else "failure"
        INVOCATION_COUNTER.labels(model_id=model_id, status=status).inc()
        INVOCATION_LATENCY.labels(model_id=model_id).observe(latency_seconds)
        
        # Store detailed metrics in repository
        metrics_repository.record_invocation(
            model_id=model_id,
            success=invoke_response.success,
            latency_ms=latency_ms,
            error_log=invoke_response.error_log,
            input_size=len(request.worklet_input.input),
            output_size=len(invoke_response.worklet_output) if invoke_response.worklet_output else 0
        )
        
        # Update gauges with latest stats
        stats = metrics_repository.get_model_stats(model_id)
        if model_id in stats:
            model_stats = stats[model_id]
            TOTAL_INVOCATIONS.labels(model_id=model_id).set(model_stats.total_invocations)
            SUCCESS_RATE.labels(model_id=model_id).set(model_stats.success_rate)
        
        return invoke_response
        
    except Exception as e:
        # Calculate metrics for failed invocation
        end_time = time.time()
        latency_seconds = end_time - start_time
        latency_ms = int(latency_seconds * 1000)
        
        # Update Prometheus metrics for failure
        INVOCATION_COUNTER.labels(model_id=model_id, status="failure").inc()
        INVOCATION_LATENCY.labels(model_id=model_id).observe(latency_seconds)
        
        # Store detailed metrics in repository
        metrics_repository.record_invocation(
            model_id=model_id,
            success=False,
            latency_ms=latency_ms,
            error_log=str(e),
            input_size=len(request.worklet_input.input),
            output_size=0
        )
        
        # Update gauges with latest stats
        stats = metrics_repository.get_model_stats(model_id)
        if model_id in stats:
            model_stats = stats[model_id]
            TOTAL_INVOCATIONS.labels(model_id=model_id).set(model_stats.total_invocations)
            SUCCESS_RATE.labels(model_id=model_id).set(model_stats.success_rate)
        
        raise HTTPException(
            status_code=500, detail=f"Error invoking model: {str(e)}"
        )
    finally:
        # Decrement active invocations gauge
        ACTIVE_INVOCATIONS.labels(model_id=model_id).dec()


# Pydantic models for metrics endpoints
class InvocationHistoryResponse(BaseModel):
    history: List[dict]
    total_count: int
    offset: int
    limit: Optional[int]


class ModelStatsResponse(BaseModel):
    stats: dict


@app.get("/metrics/history", response_model=InvocationHistoryResponse)
async def get_invocation_history(
    model_id: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: int = 0
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
        history = metrics_repository.get_invocation_history(model_id, limit, offset)
        
        # Convert to dict format
        history_dicts = [record.to_dict() for record in history]
        
        # Get total count for pagination
        total_count = metrics_repository.get_total_invocations()
        
        return InvocationHistoryResponse(
            history=history_dicts,
            total_count=total_count,
            offset=offset,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving invocation history: {str(e)}"
        )


@app.get("/metrics/stats", response_model=ModelStatsResponse)
async def get_model_stats(model_id: Optional[str] = None) -> ModelStatsResponse:
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
                    status_code=404, detail=f"No stats found for model: {model_id}"
                )
            # Convert to dict format
            stats_dict = {mid: stat.to_dict() for mid, stat in stats.items()}
        else:
            # Get stats for all models
            stats = metrics_repository.get_model_stats()
            stats_dict = {mid: stat.to_dict() for mid, stat in stats.items()}
        
        return ModelStatsResponse(stats=stats_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving model stats: {str(e)}"
        )


@app.get("/metrics")
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint for scraping.
    
    Returns:
        Response with Prometheus metrics in text format
    """
    try:
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating metrics: {str(e)}"
        )


# You can also remove graphql and do pure HTTP/REST/JSON endpoint
# https://fastapi.tiangolo.com/
graphql_app = GraphQLRouter(SCHEMA)
app.include_router(graphql_app, prefix="/graphql")
