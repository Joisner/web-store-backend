import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from httpx import Response
from typing import List, Dict, Any

from app.core.config import settings
from app import schemas
from app.services import product_service, category_service
from app.models import Product, Category, User # Import models

# --- Helper to create a category for product tests ---
@pytest.fixture(scope="function") # function scope if each test needs a clean category
def test_category(db: Session, faker_instance) -> Category:
    category_in = schemas.CategoryCreate(
        name=faker_instance.word().capitalize() + " Category",
        slug=faker_instance.slug(),
        description=faker_instance.sentence()
    )
    return category_service.create(db, obj_in=category_in)

# --- Helper to create product data ---
def get_product_create_data(category_id: int, faker_instance, **overrides) -> Dict[str, Any]:
    data = {
        "name": f"Test Product {faker_instance.uuid4()[:8]}",
        "description": faker_instance.paragraph(),
        "short_description": faker_instance.sentence(),
        "sku": f"SKU-{faker_instance.unique.ean(length=8)}",
        "slug": f"test-product-{faker_instance.slug()}-{faker_instance.uuid4()[:4]}",
        "category_id": category_id,
        "base_price": round(faker_instance.random_number(digits=4) / 100, 2) + 10, # Min price 10.00
        "stock": faker_instance.random_int(min=0, max=100),
        "status": "draft",
        "visibility": "private",
        "tags": [faker_instance.word() for _ in range(3)],
        "images": [
            {"url": faker_instance.image_url(), "alt": "Image 1", "is_main": True},
            {"url": faker_instance.image_url(), "alt": "Image 2"},
        ],
        "variants": [
            {"name": "Color", "type": "color", "value": "Red", "sku": f"SKU-SUB-RED", "stock": 10},
            {"name": "Size", "type": "size", "value": "XL", "sku": f"SKU-SUB-XL", "stock": 5, "price_override": 15.99},
        ]
    }
    data.update(overrides)
    return data

# --- Product API Tests ---

def test_create_product(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    product_data = get_product_create_data(test_category.id, faker_instance)

    response: Response = client.post(
        f"{settings.API_V1_STR}/products/",
        json=product_data,
        headers=auth_headers
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["sku"] == product_data["sku"]
    assert data["category"]["id"] == test_category.id
    assert len(data["images"]) == 2
    assert data["images"][0]["is_main"] == True
    assert len(data["variants"]) == 2
    assert data["variants"][1]["price_override"] == 15.99

    # Verify in DB
    product_db = product_service.get(db, id=data["id"])
    assert product_db is not None
    assert product_db.name == product_data["name"]
    assert len(product_db.images) == 2
    assert len(product_db.variants) == 2


def test_create_product_invalid_category(client: TestClient, auth_headers: dict, faker_instance):
    product_data = get_product_create_data(99999, faker_instance) # Non-existent category
    response: Response = client.post(
        f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers
    )
    assert response.status_code == 400
    assert "Category with id 99999 not found" in response.json()["detail"]

def test_create_product_duplicate_sku(client: TestClient, test_category: Category, auth_headers: dict, faker_instance):
    product_data1 = get_product_create_data(test_category.id, faker_instance, sku="UNIQUE-SKU-123")
    response1: Response = client.post(f"{settings.API_V1_STR}/products/", json=product_data1, headers=auth_headers)
    assert response1.status_code == 201

    product_data2 = get_product_create_data(test_category.id, faker_instance, sku="UNIQUE-SKU-123", name="Another Product")
    response2: Response = client.post(f"{settings.API_V1_STR}/products/", json=product_data2, headers=auth_headers)
    # This relies on the DB unique constraint for SKU. The service layer might not pre-check it.
    # The specific error code might be 409 (Conflict) if caught by DB, or 400 if service pre-checks.
    # The current IntegrityError handler in main.py returns 409.
    assert response2.status_code == 409, response2.text
    assert "A database integrity error occurred" in response2.json()["detail"]


def test_read_products_paginated(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    # Create a few products
    for i in range(5):
        client.post(
            f"{settings.API_V1_STR}/products/",
            json=get_product_create_data(test_category.id, faker_instance, name=f"Product Batch {i}", sku=f"SKU-BATCH-{i}", slug=f"product-batch-{i}"),
            headers=auth_headers
        )

    response: Response = client.get(f"{settings.API_V1_STR}/products/?page_offset=0&page_limit=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5 # Could be more if other tests added products
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["size"] == 3

    response_page2: Response = client.get(f"{settings.API_V1_STR}/products/?page_offset=3&page_limit=3")
    assert response_page2.status_code == 200
    data_page2 = response_page2.json()
    assert len(data_page2["items"]) >= 2 # Remaining items


def test_read_single_product_by_id(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    product_data = get_product_create_data(test_category.id, faker_instance)
    create_response = client.post(f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]

    response: Response = client.get(f"{settings.API_V1_STR}/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == product_data["name"]
    assert len(data["images"]) > 0
    assert len(data["variants"]) > 0

def test_read_single_product_by_slug(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    product_slug = f"specific-slug-for-test-{faker_instance.uuid4()[:6]}"
    product_data = get_product_create_data(test_category.id, faker_instance, slug=product_slug)
    create_response = client.post(f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers)
    assert create_response.status_code == 201

    response: Response = client.get(f"{settings.API_V1_STR}/products/{product_slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == product_slug
    assert data["name"] == product_data["name"]


def test_read_product_not_found(client: TestClient):
    response: Response = client.get(f"{settings.API_V1_STR}/products/999999") # Non-existent ID
    assert response.status_code == 404
    response_slug: Response = client.get(f"{settings.API_V1_STR}/products/non-existent-slug")
    assert response_slug.status_code == 404


def test_update_product(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    product_data = get_product_create_data(test_category.id, faker_instance)
    create_response = client.post(f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]

    update_payload = {
        "name": "Updated Product Name",
        "base_price": 99.99,
        "status": "active"
    }
    response: Response = client.put(
        f"{settings.API_V1_STR}/products/{product_id}",
        json=update_payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product Name"
    assert data["base_price"] == 99.99
    assert data["status"] == "active"
    assert data["slug"] == "updated-product-name" # Check if slug auto-updates

    product_db = product_service.get(db, id=product_id)
    assert product_db.name == "Updated Product Name"


def test_delete_product(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    product_data = get_product_create_data(test_category.id, faker_instance)
    create_response = client.post(f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]

    response: Response = client.delete(f"{settings.API_V1_STR}/products/{product_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify product is deleted from DB
    product_db = product_service.get(db, id=product_id)
    assert product_db is None

def test_delete_product_not_found(client: TestClient, auth_headers: dict):
    response: Response = client.delete(f"{settings.API_V1_STR}/products/99999", headers=auth_headers)
    assert response.status_code == 404


# --- Product Image Sub-resource Tests ---
def test_add_product_image(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    product_data = get_product_create_data(test_category.id, faker_instance, images=[]) # Create product with no images initially
    create_response = client.post(f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]

    image_payload = {"url": faker_instance.image_url(), "alt": "A new shiny image", "is_main": False}
    response: Response = client.post(
        f"{settings.API_V1_STR}/products/{product_id}/images",
        json=image_payload,
        headers=auth_headers
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["url"] == image_payload["url"]
    assert data["alt"] == image_payload["alt"]

    product_db = product_service.get(db, id=product_id)
    assert len(product_db.images) == 1
    assert product_db.images[0].alt == image_payload["alt"]

def test_delete_product_image(client: TestClient, db: Session, test_category: Category, auth_headers: dict, faker_instance):
    # Create product with one image
    initial_image_data = {"url": faker_instance.image_url(), "alt": "Image to delete", "is_main": True}
    product_data = get_product_create_data(test_category.id, faker_instance, images=[initial_image_data])
    create_response = client.post(f"{settings.API_V1_STR}/products/", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]

    # Retrieve the created product to get the image ID
    product_with_image = product_service.get(db, id=product_id)
    assert len(product_with_image.images) == 1
    image_id_to_delete = product_with_image.images[0].id

    response: Response = client.delete(
        f"{settings.API_V1_STR}/products/images/{image_id_to_delete}",
        headers=auth_headers
    )
    assert response.status_code == 200, response.text

    product_db_after_delete = product_service.get(db, id=product_id)
    assert len(product_db_after_delete.images) == 0

# TODO: Add tests for product variants sub-resources if endpoints are implemented
# TODO: Add tests for filtering products (status, featured, category_id)
# TODO: Test updating product images/variants through the main product update endpoint if that logic is complexly handled there.
# (The current product_service.update has a note that this is simplified).
