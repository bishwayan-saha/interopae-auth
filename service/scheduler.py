import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import database
from database.database import SessionLocal

logger = logging.getLogger(__name__)
def delete_revoked_refresh_tokens():
    db: Session = SessionLocal()
    logger.info("Cleaning up of revoked refresh tokens from database started")
    database.delete_refresh_tokens(db, user_id=None)

scheduler = BackgroundScheduler()
scheduler.add_job(delete_revoked_refresh_tokens, CronTrigger(minute="*/1"))
    