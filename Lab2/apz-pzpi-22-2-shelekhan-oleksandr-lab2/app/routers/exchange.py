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
    try:
        await import_data(file, db)
        return {"status": "success", "message": "Data imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export")
async def export_data_endpoint(
    db: Session = Depends(get_db), current_admin: User = Depends(role_required([Role.ADMIN]))
):
    try:
        file_path = await export_data(db, current_admin.email)
        return {"status": "success", "message": "Data exported and sent via email successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))