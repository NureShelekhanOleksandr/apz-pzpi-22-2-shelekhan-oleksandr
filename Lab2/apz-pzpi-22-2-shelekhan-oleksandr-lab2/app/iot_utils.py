from .celery_app import celery_app
from app.crud.access_code import send_smart_lock_command_admin
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.email_utils import send_email_task
from app.iot import SmartLock
from app.core.config import settings
from app.models import Property, AccessLog
from .database_task import DatabaseTask
from sqlalchemy import select
import json


def send_smart_lock_command_admin(db: AsyncSession, lock_id: str, command: str):
    """Send a command to the smart lock without booking."""
    device_id = lock_id.split(":")[0]
    encryption_key = lock_id.split(":")[1].encode()

    smart_lock = SmartLock(device_id, encryption_key)
    response = smart_lock.send_command(command)

    access_log = AccessLog(
        command=command,
        response_status=str(response.status),
        response_message=json.dumps(response.payload),
    )

    db.add(access_log)

    db.commit()

    return response


def get_properties(db):
    return db.execute(select(Property).where(Property.lock_id != None)).scalars().all()


def process_property(db, property):
    lock_id = property.lock_id
    print(f"Checking temperature for property {property.name}")
    print(f"Lock ID: {lock_id}")

    if lock_id:
        send_smart_lock_command_admin(db, lock_id, "get_temperature")
        response = send_smart_lock_command_admin(db, lock_id, "get_temperature_stats")
        anomalies = response.payload.get("anomalies")

        if anomalies:
            # write anomalies with in celcius
            anomalies = [f"{round(anomaly, 2)}°C" for anomaly in anomalies]
            send_email_task.delay(
                email_to=property.owner.email,
                subject="Temperature Anomaly Alert",
                body=f"Temperature anomalies detected for your property {property.name}: {anomalies}",
            )


@celery_app.task(
    name="check_temperature_task", bind=True, base=DatabaseTask
)
def check_temperature_task(self):
    session = self.get_session()

    properties = get_properties(session)

    print(f"Properties: {properties}")

    for property in properties:
        process_property(session, property)
