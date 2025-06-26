from sqlalchemy.orm import Session
from typing import List, Optional

from app.services.base import CRUDBase
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Category]:
        return db.query(Category).filter(Category.slug == slug).first()

    def create(self, db: Session, *, obj_in: CategoryCreate) -> Category:
        # You could add slug generation here if not provided, e.g. from name
        # from app.utils import generate_slug
        # if not obj_in.slug:
        #     obj_in.slug = generate_slug(obj_in.name)
        return super().create(db, obj_in=obj_in)

    # You can add more category-specific methods here if needed
    # For example, getting all top-level categories:
    def get_top_level_categories(self, db: Session) -> List[Category]:
        return db.query(Category).filter(Category.parent_id == None).all()

category_service = CRUDCategory(Category)
get_multi_paginated = category_service.get_multi_paginated
get_multi = category_service.get_multi
