from fastapi import FastAPI
import uvicorn
from app.routers import user, login, property, booking, payment, exchange
from app.email_utils import send_email_task

app = FastAPI()

app.include_router(user.router)
app.include_router(login.router)
app.include_router(property.router)
app.include_router(booking.router)
app.include_router(payment.router)
app.include_router(exchange.router)


@app.get("/")
def read_root(email: str):
    send_email_task(email, "Test", "This is a test email.")
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
