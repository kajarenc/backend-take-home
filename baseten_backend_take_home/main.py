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

# OpenTelemetry imports
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from baseten_backend_take_home.repositories import (
    organization_repository,
    model_repository,
)


def setup_opentelemetry():
    """Set up OpenTelemetry metrics for ClickStack
    
    Environment Variables:
    - OTEL_SERVICE_NAME: Service name for metrics (default: baseten-backend-take-home)
    - CLICKSTACK_OTLP_ENDPOINT: ClickStack OTLP endpoint (default: http://localhost:4318)
    - CLICKSTACK_OTLP_HEADERS: Headers for authentication (format: "key1=value1,key2=value2")
    
    Example configuration:
    export CLICKSTACK_OTLP_ENDPOINT="https://your-clickstack-instance:4318"
    export CLICKSTACK_OTLP_HEADERS="authorization=Bearer your-api-key"
    """

    # Create resource with service information
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "baseten-backend-take-home"),
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.SERVICE_NAMESPACE: "baseten",
    })
    
    # Configure OTLP exporter for ClickStack - prioritize standard OTel env vars
    clickstack_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv("CLICKSTACK_OTLP_ENDPOINT", "http://localhost:4318")
    clickstack_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS") or os.getenv("CLICKSTACK_OTLP_HEADERS", "")
    print("----------||||||||||||||" * 10)
    print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {clickstack_endpoint}")
    print(f"OTEL_EXPORTER_OTLP_HEADERS: {clickstack_headers}")


    headers = {}
    if clickstack_headers:
        # Parse headers from env var format: "key1=value1,key2=value2"
        for header in clickstack_headers.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
    
    # Create OTLP exporter
    exporter = OTLPMetricExporter(
        endpoint=f"{clickstack_endpoint}/v1/metrics",
        headers=headers,
        timeout=30,
    )
    
    # Create metric reader with periodic export
    reader = PeriodicExportingMetricReader(
        exporter=exporter,
        export_interval_millis=10000,  # Export every 10 seconds
        export_timeout_millis=30000,   # 30 second timeout
    )
    
    # Create and set meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )
    
    metrics.set_meter_provider(meter_provider)
    return meter_provider


# Set up OpenTelemetry
meter_provider = setup_opentelemetry()
meter = metrics.get_meter(__name__)

# Create custom metrics for the /invoke endpoint
# These metrics will be sent to ClickStack for monitoring and analysis
invoke_request_counter = meter.create_counter(
    name="invoke_requests_total",
    description="Total number of invoke requests",
    unit="1",
)

invoke_duration_histogram = meter.create_histogram(
    name="invoke_request_duration_seconds",
    description="Duration of invoke requests in seconds",
    unit="s",
)

invoke_error_counter = meter.create_counter(
    name="invoke_errors_total",
    description="Total number of invoke request errors",
    unit="1",
)

invoke_success_counter = meter.create_counter(
    name="invoke_success_total",
    description="Total number of successful invoke requests",
    unit="1",
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

MOCK_ENDPOINT = Endpoint(
    url=f"{os.getenv('MOCK_SERVER_URL', 'http://localhost:8001')}/invoke"
)


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
# Instrument FastAPI app with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


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
    
    # Increment total request counter
    invoke_request_counter.add(1, {"model_id": model_id})

    try:
        json_str = json.dumps(request.model_dump())
        response = await MOCK_ENDPOINT.exec(json_str)
        response_data = await response.json()
        invoke_response = InvokeResponse(**response_data)

        # Calculate metrics
        end_time = time.time()
        latency_seconds = end_time - start_time
        latency_ms = int(latency_seconds * 1000)
        
        # Record metrics
        invoke_duration_histogram.record(latency_seconds, {"model_id": model_id, "status": "success"})
        invoke_success_counter.add(1, {"model_id": model_id})

        return invoke_response

    except Exception as e:
        end_time = time.time()
        latency_seconds = end_time - start_time
        latency_ms = int(latency_seconds * 1000)
        
        # Record error metrics
        invoke_duration_histogram.record(latency_seconds, {"model_id": model_id, "status": "error"})
        invoke_error_counter.add(1, {"model_id": model_id, "error_type": type(e).__name__})

        raise HTTPException(
            status_code=500, detail=f"Error invoking model: {str(e)}"
        )


# You can also remove graphql and do pure HTTP/REST/JSON endpoint
# https://fastapi.tiangolo.com/
graphql_app = GraphQLRouter(SCHEMA)
app.include_router(graphql_app, prefix="/graphql")
