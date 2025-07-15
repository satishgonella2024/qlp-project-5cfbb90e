from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Union
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
    """
    Global exception handler for the application.
    Logs the error and returns a JSON response with a generic error message.
    """
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """
    Exception handler for Pydantic ValidationError.
    Logs the error and returns a JSON response with the validation errors.
    """
    logging.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )

@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    """
    Middleware to log all incoming requests and responses.
    """
    try:
        response = await call_next(request)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        raise e
    logging.info(f"Request: {request.method} {request.url} - Response: {response.status_code}")
    return response