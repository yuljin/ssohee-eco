from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead


router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionRead])
@router.get("/", response_model=List[TransactionRead])
def list_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).order_by(Transaction.executed_at.desc(), Transaction.id.desc()).all()


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    tx = Transaction(**payload.model_dump(), executed_at=datetime.utcnow())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, payload: TransactionCreate, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in payload.model_dump().items():
        setattr(tx, key, value)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    return None

