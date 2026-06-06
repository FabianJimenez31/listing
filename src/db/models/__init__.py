"""Import all ORM models so they register with Base.metadata.

Import order matters for FK resolution during create_all:
1. Independent models first (users, locations)
2. Catalogs (property types, amenities — no cross-FK)
3. Property + images (FKs to users, locations, property_types)
4. Lead (FKs to properties, users)
5. Promotions (FKs to properties, locations)
6. Engagement (FKs to properties, users)
7. SEO (standalone polymorphic)
"""
from src.db.models.user_models import UserORM, RoleORM, PermissionORM  # noqa: F401
from src.db.models.location_models import LocationORM  # noqa: F401
from src.db.models.catalog_models import PropertyTypeORM, AmenityORM, PropertyAmenityORM  # noqa: F401
from src.db.models.property_models import PropertyORM, PropertyImageORM  # noqa: F401
from src.db.models.lead_models import LeadORM  # noqa: F401
from src.db.models.promotion_models import BannerORM, FeaturedPropertyORM  # noqa: F401
from src.db.models.engagement_models import FavoriteORM, AuditLogORM, PropertyViewORM  # noqa: F401
from src.db.models.seo_models import SeoMetadataORM  # noqa: F401

__all__ = [
    "UserORM", "RoleORM", "PermissionORM",
    "LocationORM",
    "PropertyTypeORM", "AmenityORM", "PropertyAmenityORM",
    "PropertyORM", "PropertyImageORM",
    "LeadORM",
    "BannerORM", "FeaturedPropertyORM",
    "FavoriteORM", "AuditLogORM", "PropertyViewORM",
    "SeoMetadataORM",
]
