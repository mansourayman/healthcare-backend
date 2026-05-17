from fastapi import FastAPI
from .database import Base,engine;
from .routers.auth import router as auth_router
from .routers.heart_rate import router as heart_router;
from .routers.device import router as device_router
from .routers.activity import router as activity_router
from .routers.ai_activity import router as ai_activity_router
from .routers.alerts import router as alert_router
from .routers.device import router as device;

Base.metadata.create_all(bind=engine)
app=FastAPI()
app.include_router(auth_router)
app.include_router(ai_activity_router)
app.include_router(heart_router)
app.include_router(device_router)
app.include_router(activity_router);
app.include_router(alert_router)    
app.include_router(device)    

@app.get("/")
async def root():
    return {"message":"healthmonitor"}
