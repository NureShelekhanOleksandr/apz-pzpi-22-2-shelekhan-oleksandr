from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.import_export import import_data, export_data
from app.dependencies import role_required
from app.enums.user_role import Role
from app.schemas.user import User

router = APIRouter(
    prefix="/exchange",
    tags=["exchange"],
)

@router.post("/import")
async def import_data_endpoint(
    file: UploadFile = File(...), db: Session = Depends(get_db), current_admin: User = Depends(role_required([Role.ADMIN]))
):
    # Import data from the uploaded file
    # The file is uploaded by the user and passed as an argument to the function
    # The database session is also passed as an argument to the function
    # The current_admin is the user who is currently logged in and has the role of ADMIN
    try:
        await import_data(file, db)
        return {"status": "success", "message": "Data imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export")
async def export_data_endpoint(
    db: Session = Depends(get_db), current_admin: User = Depends(role_required([Role.ADMIN]))
):
    # Export data and send via email
    # The database session is passed as an argument to the function
    # The current_admin is the user who is currently logged in and has the role of ADMIN
    # The exported data is sent to the email of the current_admin
    try:
        file_path = await export_data(db, current_admin.email)
        return {"status": "success", "message": "Data exported and sent via email successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))