import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException # For catching expected HTTPExceptions if service raises them

from app.services import product_service, category_service, user_service
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.category import CategoryCreate
from app.schemas.user import UserCreate # For creating a test user
from app.models import Product, Category, User, ProductImage, ProductVariant # Import models
from app.utils import generate_slug

@pytest.fixture(scope="function")
def db_test_category(db: Session, faker_instance) -> Category:
    cat_in = CategoryCreate(
        name=f"Service Test Category - {faker_instance.word()}",
        slug=f"svc-test-cat-{faker_instance.slug()}",
        description=faker_instance.sentence()
    )
    return category_service.create(db, obj_in=cat_in)

@pytest.fixture(scope="function")
def db_test_user(db: Session, faker_instance) -> User:
    user_in = UserCreate(
        email=faker_instance.email(),
        password=faker_instance.password(),
        name=faker_instance.name()
    )
    return user_service.create(db, obj_in=user_in)


def get_sample_product_create_schema(category_id: int, faker_instance, **overrides) -> ProductCreate:
    data = {
        "name": f"Service Test Product {faker_instance.word()}",
        "description": faker_instance.paragraph(),
        "sku": f"SVC-SKU-{faker_instance.ean(length=8)}",
        "category_id": category_id,
        "base_price": round(faker_instance.random_number(digits=3) / 10, 2) + 5.0, # Min 5.00
        "stock": faker_instance.random_int(min=1, max=50),
        "slug": f"svc-test-prod-{faker_instance.slug()}",
        "images": [
            {"url": faker_instance.image_url(), "alt": "Main Image"},
            {"url": faker_instance.image_url(), "alt": "Secondary Image"}
        ],
        "variants": [
            {"name": "Color", "type": "color", "value": "Blue", "sku": f"SVC-SKU-BLUE", "stock": 5},
            {"name": "Size", "type": "size", "value": "M", "sku": f"SVC-SKU-M", "stock": 3, "price_override": 22.50}
        ]
    }
    data.update(overrides) # Apply any overrides
    return ProductCreate(**data)


def test_create_product(db: Session, db_test_category: Category, db_test_user: User, faker_instance):
    product_in = get_sample_product_create_schema(db_test_category.id, faker_instance)

    created_product = product_service.create(db, obj_in=product_in, created_by_user_id=db_test_user.id)

    assert created_product is not None
    assert created_product.name == product_in.name
    assert created_product.sku == product_in.sku
    assert created_product.category_id == db_test_category.id
    assert created_product.created_by_user_id == db_test_user.id
    assert created_product.slug == generate_slug(product_in.slug) # Service cleans slug

    # Verify in DB
    product_from_db = db.query(Product).filter(Product.id == created_product.id).first()
    assert product_from_db is not None
    assert product_from_db.name == product_in.name

    # Check images and variants were created and associated (basic check)
    assert len(created_product.images) == 2
    assert created_product.images[0].alt == "Main Image"
    assert len(created_product.variants) == 2
    assert created_product.variants[0].value == "Blue"

    # Ensure that refresh in service loaded these relationships
    assert len(product_from_db.images) == 2
    assert len(product_from_db.variants) == 2


def test_create_product_generates_slug_if_not_provided(db: Session, db_test_category: Category, faker_instance):
    product_name = "A Product Name Needing a Slug"
    product_in = get_sample_product_create_schema(
        db_test_category.id,
        faker_instance,
        name=product_name,
        slug="" # Explicitly empty slug
    )

    created_product = product_service.create(db, obj_in=product_in)
    assert created_product.slug == generate_slug(product_name)


def test_get_product_by_slug(db: Session, db_test_category: Category, faker_instance):
    target_slug = f"find-me-slug-{faker_instance.uuid4()[:4]}"
    product_in = get_sample_product_create_schema(db_test_category.id, faker_instance, slug=target_slug)
    product_service.create(db, obj_in=product_in)

    found_product = product_service.get_product_by_slug(db, slug=target_slug)
    assert found_product is not None
    assert found_product.slug == target_slug
    assert found_product.category is not None # Check eager loading
    assert len(found_product.images) > 0 # Check subquery loading for images
    assert len(found_product.variants) > 0 # Check subquery loading for variants

    assert product_service.get_product_by_slug(db, slug="non-existent-slug") is None


def test_update_product(db: Session, db_test_category: Category, db_test_user: User, faker_instance):
    product_in = get_sample_product_create_schema(db_test_category.id, faker_instance, name="Original Product")
    db_product = product_service.create(db, obj_in=product_in, created_by_user_id=db_test_user.id)

    update_data_dict = {
        "name": "Updated Service Product",
        "base_price": 123.45,
        "status": "active",
        "description": "This is an updated description."
        # Not updating images/variants here as service update is simplified for them
    }
    # Using dict for obj_in as service update method allows it
    updated_product = product_service.update(
        db,
        db_obj=db_product,
        obj_in=update_data_dict,
        last_modified_by_user_id=db_test_user.id
    )

    assert updated_product.name == "Updated Service Product"
    assert updated_product.base_price == 123.45
    assert updated_product.status == "active"
    assert updated_product.description == "This is an updated description."
    assert updated_product.last_modified_by_user_id == db_test_user.id
    # Slug should auto-update if name changes and slug not explicitly provided in update
    assert updated_product.slug == generate_slug("Updated Service Product")


def test_manage_product_images(db: Session, db_test_category: Category, faker_instance):
    product_in = get_sample_product_create_schema(db_test_category.id, faker_instance, images=[]) # No initial images
    product = product_service.create(db, obj_in=product_in)

    # Add an image
    img_create_schema = schemas.ProductImageCreate(url=faker_instance.image_url(), alt="Test Image 1")
    added_image = product_service.add_product_image(db, product=product, image_in=img_create_schema)
    assert added_image is not None
    assert added_image.alt == "Test Image 1"
    assert added_image.product_id == product.id

    db.refresh(product) # Refresh product to see the new image in its relationships
    assert len(product.images) == 1

    # Update the image
    img_update_schema = schemas.ProductImageUpdate(alt="Updated Test Image 1 Alt")
    updated_image = product_service.update_product_image(db, image_db=added_image, image_in=img_update_schema)
    assert updated_image.alt == "Updated Test Image 1 Alt"

    # Get the image
    retrieved_image = product_service.get_product_image(db, image_id=added_image.id)
    assert retrieved_image is not None
    assert retrieved_image.alt == "Updated Test Image 1 Alt"

    # Remove the image
    removed_image = product_service.remove_product_image(db, image_id=added_image.id)
    assert removed_image is not None
    assert product_service.get_product_image(db, image_id=added_image.id) is None

    db.refresh(product)
    assert len(product.images) == 0


# TODO: Test get_multi_paginated with various filters
# TODO: Test for IntegrityError (e.g., duplicate SKU on create, if service pre-checked or if DB raises it)
# The current service create method doesn't explicitly pre-check SKU uniqueness, relying on DB constraints.
# So, testing that would involve catching the IntegrityError from the database.
# Example:
# def test_create_product_duplicate_sku_service_level(db: Session, db_test_category: Category, faker_instance):
#     sku = "SVC-DUPE-SKU-001"
#     product1_in = get_sample_product_create_schema(db_test_category.id, faker_instance, sku=sku)
#     product_service.create(db, obj_in=product1_in)
#
#     product2_in = get_sample_product_create_schema(db_test_category.id, faker_instance, sku=sku, name="Another product same SKU")
#     with pytest.raises(Exception): # Replace with specific exception if service throws one, or IntegrityError if testing DB constraint
#         product_service.create(db, obj_in=product2_in)

# TODO: Test product variant management services if they are added (add_product_variant, etc.)
# TODO: Test deletion of product and ensure cascade deletion of images/variants works as expected if configured.
# CRUDBase.remove is used; cascade is a DB/model-level concern.
# If Product model has `cascade="all, delete-orphan"` for images/variants, they should be deleted.
# A test could verify this:
# 1. Create product with images/variants.
# 2. Delete product.
# 3. Query ProductImage/ProductVariant tables to ensure related items are gone.
