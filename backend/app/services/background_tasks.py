import time
import inspect
import asyncio
from typing import Callable, Any, Dict, Optional
from datetime import datetime, timezone
from app.core.logging import logger
from app.database import SessionLocal


def execute_background_task(task_name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Safe wrapper for executing asynchronous or synchronous background tasks.
    Ensures background exceptions are caught, logged with structured metrics,
    and never crash the main application process.
    """
    start_time = time.time()
    task_id = f"{task_name}_{int(start_time * 1000)}"
    logger.info(f"[BackgroundTask:START] task_id={task_id} name='{task_name}'")

    result = None
    success = False
    error_msg = None

    try:
        if inspect.iscoroutinefunction(func):
            # If called within an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    result = loop.create_task(func(*args, **kwargs))
                else:
                    result = loop.run_until_complete(func(*args, **kwargs))
            except Exception:
                result = asyncio.run(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)

        success = True
    except Exception as exc:
        error_msg = str(exc)
        logger.error(f"[BackgroundTask:ERROR] task_id={task_id} name='{task_name}' error='{error_msg}'", exc_info=True)

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    status_str = "SUCCESS" if success else "FAILED"
    logger.info(f"[BackgroundTask:{status_str}] task_id={task_id} name='{task_name}' elapsed_ms={elapsed_ms}")

    return {
        "task_id": task_id,
        "task_name": task_name,
        "success": success,
        "elapsed_ms": elapsed_ms,
        "error": error_msg,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =========================================================================
# Standard Production Background Jobs
# =========================================================================

def background_verify_ledger():
    """Background task to verify blockchain-style hash chain integrity."""
    from app.services.blockchain_service import blockchain_service
    db = SessionLocal()
    try:
        res = blockchain_service.verify_chain_integrity(db=db)
        logger.info(f"[BackgroundTask:LedgerVerify] Chain valid: {res.get('is_valid', True)}, verified {res.get('total_blocks', 0)} blocks")
        return res
    finally:
        db.close()


def background_log_notification(user_id: str, title: str, notification_type: str):
    """Background notification metrics logger."""
    logger.info(f"[BackgroundTask:Notification] Dispatched to user={user_id} type='{notification_type}' title='{title}'")


def background_refresh_analytics():
    """Background worker job to pre-compute analytics aggregation counters."""
    from app.models.relief_request import ReliefRequest
    from app.models.distribution import Distribution
    db = SessionLocal()
    try:
        total_reqs = db.query(ReliefRequest).count()
        total_dists = db.query(Distribution).count()
        logger.info(f"[BackgroundTask:Analytics] Synced counters: requests={total_reqs}, distributions={total_dists}")
        return {"total_requests": total_reqs, "total_distributions": total_dists}
    finally:
        db.close()
