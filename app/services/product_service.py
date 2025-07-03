from sqlalchemy.orm import Session, joinedload, subqueryload
from typing import Any, Dict, List, Optional, Union, Tuple

from app.services.base import CRUDBase
from app.models.product import Product, ProductVariant
from app.models.product_image import ProductImage
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.product_image import ProductImageCreate, ProductImageUpdate
from app.schemas.product_variant import ProductVariantCreate, ProductVariantUpdate
from app.utils import generate_slug # Assuming you'll create this utility

class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):

    def get_product_by_slug(self, db: Session, *, slug: str) -> Optional[Product]:
        return db.query(Product).filter(Product.slug == slug).options(
            joinedload(Product.category),
            subqueryload(Product.images),
            subqueryload(Product.variants)
        ).first()

    def get(self, db: Session, id: Any) -> Optional[Product]:
        return db.query(self.model).filter(self.model.id == id).options(
            joinedload(self.model.category),
            subqueryload(self.model.images),
            subqueryload(self.model.variants)
        ).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Product]:
        return db.query(self.model).order_by(self.model.id.desc()).offset(skip).limit(limit).options(
            joinedload(self.model.category),
            # subqueryload(self.model.images), # Maybe not load all images/variants for list view
            # subqueryload(self.model.variants)
        ).all()

    def get_multi_paginated(
        self, db: Session, *, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Product], int]:
        query = db.query(self.model)

        if filters:
            if "category_id" in filters and filters["category_id"]:
                query = query.filter(self.model.category_id == filters["category_id"])
            if "status" in filters and filters["status"]:
                query = query.filter(self.model.status == filters["status"])
            if "featured" in filters and filters["featured"] is not None:
                query = query.filter(self.model.featured == filters["featured"])
            # Add more filters as needed: name search, price range, etc.

        total = query.count()
        items = query.order_by(self.model.id.desc()).offset(skip).limit(limit).options(
            joinedload(self.model.category),
        ).all()
        return items, total

    def create(self, db: Session, *, obj_in: ProductCreate, created_by_user_id: Optional[int] = None) -> Product:
        # Auto-generate slug if not provided or ensure it's unique
        if not obj_in.slug:
            obj_in.slug = generate_slug(obj_in.name)
        else:
            obj_in.slug = generate_slug(obj_in.slug) # Clean the provided slug

        # Basic product data
        product_data = obj_in.model_dump(exclude={"images", "variants"})

        db_product = Product(**product_data, created_by_user_id=created_by_user_id, last_modified_by_user_id=created_by_user_id)

        # Handle images
        if obj_in.images:
            for img_data in obj_in.images:
                db_img = ProductImage(**img_data.model_dump(), product=db_product)
                # db.add(db_img) # Not needed if cascade is set up correctly and added to product.images

        # Handle variants
        if obj_in.variants:
            for var_data in obj_in.variants:
                variant_dict = var_data.model_dump() if hasattr(var_data, "model_dump") else dict(var_data)
                # Asegúrate de que attributes sea un dict (no None ni string)
                if "attributes" in variant_dict and variant_dict["attributes"] is not None:
                    if not isinstance(variant_dict["attributes"], dict):
                        try:
                            import json
                            variant_dict["attributes"] = json.loads(variant_dict["attributes"])
                        except Exception:
                            variant_dict["attributes"] = {}
                db_var = ProductVariant(**variant_dict)
                db_product.variants.append(db_var)  # <-- Esto ya lo tienes, es correcto

        try:
            db.add(db_product)
            db.commit()
            db.refresh(db_product)
            db.refresh(db_product, attribute_names=['images', 'variants', 'category'])
            return db_product
        except Exception as e:
            db.rollback()
            # Log error e
            raise e


    def update(
        self,
        db: Session,
        *,
        db_obj: Product,
        obj_in: Union[ProductUpdate, Dict[str, Any]],
        last_modified_by_user_id: Optional[int] = None
    ) -> Product:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"]:
            update_data["slug"] = generate_slug(update_data["slug"])
        elif "name" in update_data and db_obj.name != update_data["name"]: # Auto-update slug if name changes and slug not given
            if "slug" not in update_data or not update_data.get("slug"):
                 update_data["slug"] = generate_slug(update_data["name"])


        # Update product fields
        for field in update_data:
            if hasattr(db_obj, field) and field not in ["images", "variants"]: # Handle images/variants separately
                setattr(db_obj, field, update_data[field])

        db_obj.last_modified_by_user_id = last_modified_by_user_id

        # Note: Updating images and variants here can be complex.
        # For simplicity, this example doesn't fully implement deep updates of images/variants.
        # A more robust solution would involve:
        # 1. Identifying images/variants to be added, updated, or deleted.
        # 2. Handling them through dedicated service methods or logic here.
        # Example: If images are passed in ProductUpdate, you might clear existing and add new ones.
        # if "images" in update_data:
        #     # Clear existing images
        #     for img in list(db_obj.images): # Iterate over a copy
        #         db.delete(img)
        #     db.flush() # Process deletions
        #     # Add new images
        #     for img_data_dict in update_data["images"]:
        #         img_data = ProductImageCreate(**img_data_dict) # Assuming it's create schema
        #         new_img = ProductImage(**img_data.model_dump(), product_id=db_obj.id)
        #         db.add(new_img)

        # Similar logic for variants

        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            db.refresh(db_obj, attribute_names=['images', 'variants', 'category'])
            return db_obj
        except Exception as e:
            db.rollback()
            raise e

    # Methods for managing Product Images (example)
    def add_product_image(self, db: Session, *, product: Product, image_in: ProductImageCreate) -> ProductImage:
        # Solo pasa los campos válidos para ProductImage
        image_data = image_in.model_dump()
        image_data.pop("filename", None)  # Elimina filename si existe
        db_image = ProductImage(**image_data, product_id=product.id)
        try:
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            return db_image
        except Exception as e:
            db.rollback()
            raise e

    def update_product_image(self, db: Session, *, image_db: ProductImage, image_in: ProductImageUpdate) -> ProductImage:
        update_data = image_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(image_db, field, value)
        try:
            db.add(image_db)
            db.commit()
            db.refresh(image_db)
            return image_db
        except Exception as e:
            db.rollback()
            raise e

    def get_product_image(self, db: Session, *, image_id: int) -> Optional[ProductImage]:
        return db.query(ProductImage).filter(ProductImage.id == image_id).first()

    def remove_product_image(self, db: Session, *, image_id: int) -> Optional[ProductImage]:
        image = self.get_product_image(db, image_id=image_id)
        if image:
            try:
                db.delete(image)
                db.commit()
                return image
            except Exception as e:
                db.rollback()
                raise e
        return None

    # Similar methods for Product Variants can be added here:
    # add_product_variant, update_product_variant, get_product_variant, remove_product_variant

product_service = CRUDProduct(Product)
get_multi_paginated = product_service.get_multi_paginated
create = product_service.create
get = product_service.get
update = product_service.update
add_product_image = product_service.add_product_image
add_product_image = product_service.add_product_image
add_product_image = product_service.add_product_image