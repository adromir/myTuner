"""Background scheduler for refreshing dynamic M3U and Podcast sources.

Uses APScheduler to periodically fetch and cache source content.
"""
import logging
import json
import traceback
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from .providers import get_provider

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_dynamic_sources():
    """Background task to fetch and parse M3U and Podcast sources, then store them in SourceCache."""
    db: Session = SessionLocal()
    try:
        sources = db.query(models.Source).filter(models.Source.provider.in_(['m3u', 'podcast'])).all()
        for source in sources:
            try:
                config = json.loads(source.config) if source.config else {}
                url = config.get("url")
                if not url:
                    continue

                provider = get_provider(source.provider)
                if not provider:
                    logger.warning(f"No provider found for source {source.id} ({source.provider})")
                    continue

                items = provider.browse_folder({"url": url}, node_id=f"src_{source.id}")

                # Upsert cache
                cache = db.query(models.SourceCache).filter(models.SourceCache.source_id == source.id).first()
                if cache:
                    cache.data = json.dumps(items)
                else:
                    cache = models.SourceCache(source_id=source.id, data=json.dumps(items))
                    db.add(cache)
                db.commit()
                logger.info(f"Refreshed source {source.id} ({source.name}): {len(items)} items")
            except Exception as e:
                logger.error(f"Error refreshing source {source.id} ({source.name}): {e}")
                logger.error(traceback.format_exc())
                db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Initialize and start the background scheduler."""
    db: Session = SessionLocal()
    try:
        setting = db.query(models.Settings).filter(models.Settings.key == "background_refresh_interval").first()
        interval_minutes = int(setting.value) if setting else 60
    except Exception:
        interval_minutes = 60
    finally:
        db.close()

    scheduler.add_job(
        refresh_dynamic_sources,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="refresh_dynamic_sources",
        name="Refresh dynamic sources",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Run once immediately on startup
    scheduler.add_job(
        refresh_dynamic_sources,
        id="initial_refresh_dynamic_sources",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Started background scheduler with {interval_minutes} minutes interval.")


def update_scheduler_interval(minutes: int):
    """Update the refresh interval of the running scheduler."""
    scheduler.reschedule_job(
        "refresh_dynamic_sources",
        trigger=IntervalTrigger(minutes=minutes)
    )
    logger.info(f"Updated background scheduler interval to {minutes} minutes.")
