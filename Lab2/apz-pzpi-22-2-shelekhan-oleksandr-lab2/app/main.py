from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routers import (
    user,
    login,
    property,
    booking,
    payment,
    exchange,
    access_code,
    notification,
)
from app.email_utils import send_email_task

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(login.router)
app.include_router(property.router)
app.include_router(booking.router)
app.include_router(payment.router)
app.include_router(exchange.router)
app.include_router(access_code.router)
app.include_router(notification.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Booking API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
