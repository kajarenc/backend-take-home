# worklet_mock_server is a mock server for the remote
# basten API, you can test locally with it using the MOCK_ENDPOINT
# predefined in the project.
#
# **Note to challengers:**
# You do not need to modify this

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI
import secrets
import time

app = FastAPI()


class PostModelInvokeRequestWorkletInput(BaseModel):
    model_id: str
    input: List[int]


class PostModelInvokeRequest(BaseModel):
    worklet_input: PostModelInvokeRequestWorkletInput


class PostModelInvokeResponse(BaseModel):
    latency_ms: int | float

    success: bool = Field(default_factory=lambda: True)
    error_log: Optional[str] = Field(default_factory=lambda: "")
    worklet_output: list[int] = Field(default_factory=list)


@app.post("/invoke", response_model=PostModelInvokeResponse)
async def post_model_invoke(request: PostModelInvokeRequest):
    latency_ms = secrets.randbelow(100)
    # Fake invoke
    time.sleep(0.01 * latency_ms)

    # Randomly fail
    # You might also see this on the real endpoint 🥲
    if percentage_bool(10):
        return PostModelInvokeResponse(
            latency_ms=latency_ms,
            success=False,
            error_log=secrets.choice(
                [
                    "There was a Network error while calling the model",
                    f"Model {request.worklet_input.model_id} is not deployed",
                    f"Model {request.worklet_input.model_id} does not exist",
                ]
            ),
        )

    return PostModelInvokeResponse(
        latency_ms=latency_ms,
        worklet_output=[int(x * 2 / 3) for x in request.worklet_input.input],
    )


@app.get("/healtz")
async def health_check():
    return {"status": "healthy", "service": "worklet-mock-server"}


# p must be 0 and 100
# 100 will always return true
# 0 will always return false
def percentage_bool(p: int) -> bool:
    if p > secrets.randbelow(100):
        return True
    return False
