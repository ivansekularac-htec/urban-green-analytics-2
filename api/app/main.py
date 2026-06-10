# Minimal FastAPI application created to validate local development environment setup.
# This endpoint serves as a temporary health-check during initial project setup.

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Urbangreen API"}