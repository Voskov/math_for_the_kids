from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Kid, KidTopicLevel

router = APIRouter(prefix="/kids", tags=["kids"])


class TopicLevelOut(BaseModel):
    topic: str
    difficulty_level: float
    score_accumulator: float

    model_config = {"from_attributes": True}


class KidOut(BaseModel):
    id: int
    name: str
    avatar_emoji: str
    starting_grade: str
    levels: list[TopicLevelOut]

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[KidOut])
def list_kids(db: Session = Depends(get_db)):
    return db.query(Kid).all()


@router.get("/{kid_id}", response_model=KidOut)
def get_kid(kid_id: int, db: Session = Depends(get_db)):
    kid = db.get(Kid, kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    return kid
