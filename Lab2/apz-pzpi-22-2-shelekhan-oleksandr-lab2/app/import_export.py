import csv
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from app.models import User, Property, Booking, Payment, AccessCode
from app.schemas import (
    UserFull as UserSchema,
    Property as PropertySchema,
    Booking as BookingSchema,
    Payment as PaymentSchema,
    # AccessLog as AccessLogSchema,
    AccessCode as AccessCodeSchema,
)
from io import BytesIO
import pandas as pd
import os
from enum import Enum
from datetime import datetime
from app.email_utils import send_email_task

def get_data():
    """Get models and schemas for data import/export."""
    models = [User, Property, Booking, Payment, AccessCode]
    schemas = [UserSchema, PropertySchema, BookingSchema, PaymentSchema, AccessCodeSchema]
    return models, schemas


async def reset_sequence(db: Session, table_name: str):
    """Reset the sequence for a table."""
    query = text(f"""
        SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), MAX(id))
        FROM {table_name};
    """)
    await db.execute(query)
    await db.commit()


async def import_data(file, db: Session):
    """Import data from an Excel file."""
    # Read the contents of the uploaded file
    contents = await file.read()
    # Load the Excel file into a dictionary of DataFrames
    sheets = pd.read_excel(BytesIO(contents), sheet_name=None)
    
    # Get the models and schemas for data import
    models, schemas = get_data()

    # Iterate over each model and schema
    for model, schema in zip(models, schemas):
        sheet_name = model.__name__
        if sheet_name in sheets:
            df = sheets[sheet_name]
            # Iterate over each row in the DataFrame
            for _, row in df.iterrows():
                data = row.to_dict()
                record_id = data.get("id")
                existing_record = await db.get(model, record_id)
                if existing_record:
                    # Update the existing record
                    updated_record = schema(**data)
                    for key, value in updated_record.dict(exclude={"id"}).items():
                        setattr(existing_record, key, value)
                else:
                    # Create a new record
                    new_record = schema(**data)
                    db.add(model(**new_record.dict()))
                await db.commit()

    # Reset the sequence for each model
    for model in models:
        await reset_sequence(db, model.__tablename__)

async def export_data(db: Session, user_email: str):
    """Export data to an Excel file and send via email."""
    # Create a BytesIO object to hold the Excel file
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    # Get the models and schemas for data export
    models, schemas = get_data()
    # Iterate over each model and schema
    for model, schema in zip(models, schemas):
        records = await db.execute(select(model))
        data = []
        # Iterate over each record in the database
        for record in records.scalars():
            record_dict = schema.from_orm(record).__dict__
            for key, value in record_dict.items():
                if isinstance(value, Enum):
                    record_dict[key] = value.value
            data.append(record_dict)
        # Convert the data to a DataFrame and write to the Excel file
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=model.__name__, index=False)
    writer.close()
    output.seek(0)
    file_path = f"exported_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    # Write the Excel file to disk
    with open(file_path, "wb") as f:
        f.write(output.getvalue())
    
    # Send the file via email
    send_email_task.delay(user_email, "Exported Data", "Please find the exported data attached.", file_path)
    
    return file_path
