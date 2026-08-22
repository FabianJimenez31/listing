"""Import all ORM models so they register with Base.metadata.

Import order matters for FK resolution during create_all:
1. Independent models first (users, locations)
2. Catalogs (property types, amenities — no cross-FK)
3. Property + images (FKs to users, locations, property_types)
4. Lead (FKs to properties, users)
5. Promotions (FKs to properties, locations)
6. Engagement (FKs to properties, users)
7. SEO (standalone polymorphic)
8. Site settings (singleton; FK to users)
"""
from src.db.models.user_models import UserORM, RoleORM, PermissionORM  # noqa: F401
from src.db.models.login_otp_models import LoginOtpORM  # noqa: F401
from src.db.models.location_models import LocationORM  # noqa: F401
from src.db.models.agency_models import AgencyORM  # noqa: F401
from src.db.models.catalog_models import PropertyTypeORM, AmenityORM, PropertyAmenityORM  # noqa: F401
from src.db.models.property_models import PropertyORM, PropertyImageORM  # noqa: F401
from src.db.models.project_models import ProjectORM, ProjectImageORM  # noqa: F401
from src.db.models.lead_models import LeadORM  # noqa: F401
from src.db.models.promotion_models import BannerORM, FeaturedPropertyORM  # noqa: F401
from src.db.models.engagement_models import FavoriteORM, AuditLogORM, PropertyViewORM  # noqa: F401
from src.db.models.partner_models import PartnerORM  # noqa: F401
from src.db.models.blog_models import PostORM  # noqa: F401
from src.db.models.seo_models import SeoMetadataORM  # noqa: F401
from src.db.models.site_settings_models import SiteSettingsORM  # noqa: F401
from src.db.models.tour_payment_models import TourPaymentORM  # noqa: F401
from src.db.models.virtual_tour_models import (  # noqa: F401
    VirtualTourGenerationAttemptORM,
    VirtualTourHotspotORM,
    VirtualTourORM,
    VirtualTourSceneORM,
)

__all__ = [
    "UserORM", "RoleORM", "PermissionORM",
    "LoginOtpORM",
    "LocationORM",
    "AgencyORM",
    "PropertyTypeORM", "AmenityORM", "PropertyAmenityORM",
    "PropertyORM", "PropertyImageORM",
    "ProjectORM", "ProjectImageORM",
    "LeadORM",
    "BannerORM", "FeaturedPropertyORM",
    "FavoriteORM", "AuditLogORM", "PropertyViewORM",
    "PartnerORM", "PostORM",
    "SeoMetadataORM",
    "SiteSettingsORM",
    "VirtualTourORM", "VirtualTourSceneORM", "TourPaymentORM", "VirtualTourHotspotORM",
    "VirtualTourGenerationAttemptORM",
]
