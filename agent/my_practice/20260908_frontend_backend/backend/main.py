import math

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class SquareRequest(BaseModel):
    x: float


class SquareResponse(BaseModel):
    x: float
    square: float


app = FastAPI(title="Square API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/square", response_model=SquareResponse)
def square_number(request: SquareRequest) -> SquareResponse:
    if not math.isfinite(request.x):
        raise HTTPException(status_code=422, detail="x must be a finite number")

    return SquareResponse(x=request.x, square=request.x**2)
