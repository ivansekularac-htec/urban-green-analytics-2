from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Urban Green API is running"}
