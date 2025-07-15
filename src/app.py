from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logging.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )

@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        raise e
    logging.info(f"Request: {request.method} {request.url} - Response: {response.status_code}")
    return response