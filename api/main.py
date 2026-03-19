from fastapi import FastAPI
from api.routers import upload, migrate, status, results, download
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4566"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(migrate.router)
app.include_router(status.router)
app.include_router(results.router)
app.include_router(download.router)
