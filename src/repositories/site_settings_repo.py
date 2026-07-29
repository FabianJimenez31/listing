"""Repository for the SiteSettings singleton."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models.site_settings_models import SINGLETON_ID, SiteSettingsORM


class SiteSettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self) -> SiteSettingsORM:
        """Return the singleton settings row, creating an empty one on first use."""
        settings = self.db.get(SiteSettingsORM, SINGLETON_ID)
        if settings is None:
            settings = SiteSettingsORM(id=SINGLETON_ID)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings
