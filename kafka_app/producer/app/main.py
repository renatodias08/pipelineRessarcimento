import logging

import brotli
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, APIRouter, Query, Request
from app.config import get_settings
import json
import uuid

log = logging.getLogger("uvicorn")

router = APIRouter(prefix="/v1")


async def compress(message: str) -> bytes:

    return brotli.compress(
        bytes(message, get_settings().file_encoding),
        quality=get_settings().file_compression_quality,
    )



@router.post("/ressarcimento")
async def produce_message(request: Request):
    request_uuid = str(uuid.uuid4())
    request_body = await request.json()
    request_body["uuid"] = request_uuid
    await producer.send_and_wait("jobs", await compress(json.dumps(request_body)))
    return request_body

    
@router.post("/teste")
async def produce_message(message: str = Query(...)) -> dict:
    return await producer.send_and_wait("jobs", await compress(message))


def create_application() -> FastAPI:
    """Create FastAPI application and set routes.

    Returns:
        FastAPI: The created FastAPI instance.
    """

    application = FastAPI(openapi_url="/kafka_producer/openapi.json", docs_url="/kafka_producer/docs")
    application.include_router(router, tags=["producer"])
    return application


def create_producer() -> AIOKafkaProducer:

    return AIOKafkaProducer(
        bootstrap_servers=get_settings().kafka_instance,
    )


app = create_application()
producer = create_producer()


@app.on_event("startup")
async def startup_event():
    """Start up event for FastAPI application."""
    log.info("Starting up...")
    await producer.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for FastAPI application."""

    log.info("Shutting down...")
    await producer.stop()

