#!/usr/bin/env python
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter

import aiohttp
import strawberry

from repositories import organization_repository, model_repository


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

MOCK_ENDPOINT = Endpoint(url="http://localhost:8001/invoke")


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

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    return """
        Welcome to baseten_take_home invoker,
        go to <a href="/graphql">/graphql</a> for the API doc
    """


# You can also remove graphql and do pure HTTP/REST/JSON endpoint
# https://fastapi.tiangolo.com/
graphql_app = GraphQLRouter(SCHEMA)
app.include_router(graphql_app, prefix="/graphql")
