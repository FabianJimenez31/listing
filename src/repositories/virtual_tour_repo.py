"""Database queries for virtual tours and their ordered scene graph."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from src.db.models.virtual_tour_models import VirtualTourORM, VirtualTourSceneORM
from src.repositories.base import BaseRepository


class VirtualTourRepository(BaseRepository[VirtualTourORM]):
    def __init__(self, db: Session) -> None:
        super().__init__(VirtualTourORM, db)

    @staticmethod
    def _owner_filter(entity: str, entity_id: str):
        if entity == "properties":
            return VirtualTourORM.property_id == entity_id
        if entity == "projects":
            return VirtualTourORM.project_id == entity_id
        raise ValueError("entity must be 'properties' or 'projects'")

    def get_for_entity(self, entity: str, entity_id: str) -> VirtualTourORM | None:
        stmt = (
            select(VirtualTourORM)
            .where(self._owner_filter(entity, entity_id))
            .options(
                selectinload(VirtualTourORM.scenes).selectinload(
                    VirtualTourSceneORM.hotspots
                )
            )
        )
        return self.db.scalar(stmt)

    def get_published(self, entity: str, entity_id: str) -> VirtualTourORM | None:
        stmt = (
            select(VirtualTourORM)
            .where(
                self._owner_filter(entity, entity_id),
                VirtualTourORM.status == "published",
            )
            .options(
                selectinload(VirtualTourORM.scenes).selectinload(
                    VirtualTourSceneORM.hotspots
                )
            )
        )
        return self.db.scalar(stmt)

    def get_scene(self, scene_id: str) -> VirtualTourSceneORM | None:
        stmt = (
            select(VirtualTourSceneORM)
            .where(VirtualTourSceneORM.id == scene_id)
            .options(
                joinedload(VirtualTourSceneORM.tour),
                selectinload(VirtualTourSceneORM.hotspots),
            )
        )
        return self.db.scalar(stmt)
