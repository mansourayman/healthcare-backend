from fastapi import FastAPI

from database import Base, engine

from routers import auth
from routers import device
from routers import heart_rate
from routers import activity
from routers import ai_activity
from routers import alerts
from routers import user_activity

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Healthcare Backend",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(device.router)
app.include_router(heart_rate.router)
app.include_router(activity.router)
app.include_router(ai_activity.router)
app.include_router(alerts.router)
app.include_router(user_activity.router)


@app.get("/")
def root():
    return {
        "message": "Healthcare Backend Running"
    }
