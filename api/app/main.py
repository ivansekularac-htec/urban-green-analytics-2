from fastapi import FastAPI

app = FastAPI(title="Urban Green API")


@app.get("/")
def root():
    return {"message": "Hello, Urban Green API!"}
