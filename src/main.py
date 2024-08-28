from fastapi import FastAPI

from src.users.router import router as users_router

app = FastAPI()


@app.get("/")
def root():
    return "localhost:8000/docs#/"


app.include_router(users_router)
