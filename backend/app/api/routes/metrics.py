from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.metrics import metrics_response, refresh_runtime_gauges, sync_derived_counters

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics(request: Request, session: Session = Depends(get_db)):
    if getattr(request.state, 'public_demo', True):
        raise HTTPException(status_code=404, detail="Not found")
    sync_derived_counters(session)
    refresh_runtime_gauges(session)
    return metrics_response()
