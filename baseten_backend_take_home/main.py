#!/usr/bin/env python
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter
import time

import aiohttp
import strawberry
import json
import os

from baseten_backend_take_home.repositories import organization_repository, model_repository
from baseten_backend_take_home.prometheus_metrics import MetricsCollector, MetricsEndpoints

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
    MetricsCollector.increment_active_invocations(model_id)
    
    try:
        json_str = json.dumps(request.model_dump())
        response = await MOCK_ENDPOINT.exec(json_str)
        response_data = await response.json()
        invoke_response = InvokeResponse(**response_data)
        
        # Calculate metrics
        end_time = time.time()
        latency_seconds = end_time - start_time
        latency_ms = int(latency_seconds * 1000)
        
        # Record metrics using the metrics collector
        MetricsCollector.record_invocation_metrics(
            model_id=model_id,
            success=invoke_response.success,
            latency_seconds=latency_seconds,
            latency_ms=latency_ms,
            error_log=invoke_response.error_log,
            input_size=len(request.worklet_input.input),
            output_size=len(invoke_response.worklet_output) if invoke_response.worklet_output else 0
        )
        
        return invoke_response
        
    except Exception as e:
        # Calculate metrics for failed invocation
        end_time = time.time()
        latency_seconds = end_time - start_time
        latency_ms = int(latency_seconds * 1000)
        
        # Record metrics for failed invocation
        MetricsCollector.record_invocation_metrics(
            model_id=model_id,
            success=False,
            latency_seconds=latency_seconds,
            latency_ms=latency_ms,
            error_log=str(e),
            input_size=len(request.worklet_input.input),
            output_size=0
        )
        
        raise HTTPException(
            status_code=500, detail=f"Error invoking model: {str(e)}"
        )
    finally:
        # Decrement active invocations gauge
        MetricsCollector.decrement_active_invocations(model_id)


# Metrics endpoints using the MetricsEndpoints class
@app.get("/metrics/history")
async def get_invocation_history(
    model_id: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: int = 0
):
    return await MetricsEndpoints.get_invocation_history(model_id, limit, offset)


@app.get("/metrics/stats")
async def get_model_stats(model_id: Optional[str] = None):
    return await MetricsEndpoints.get_model_stats(model_id)


@app.get("/metrics")
async def get_prometheus_metrics():
    return await MetricsEndpoints.get_prometheus_metrics()


# You can also remove graphql and do pure HTTP/REST/JSON endpoint
# https://fastapi.tiangolo.com/
graphql_app = GraphQLRouter(SCHEMA)
app.include_router(graphql_app, prefix="/graphql")
