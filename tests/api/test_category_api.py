import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from httpx import Response
from typing import Dict, Any

from app.core.config import settings
from app import schemas
from app.services import category_service
from app.models import Category # Import Category model

# Helper to create category data
def get_category_create_data(faker_instance, **overrides) -> Dict[str, Any]:
    data = {
        "name": f"Category {faker_instance.word().capitalize()} {faker_instance.uuid4()[:4]}",
        "slug": f"cat-{faker_instance.slug()}-{faker_instance.uuid4()[:4]}",
        "description": faker_instance.sentence(),
        "color": faker_instance.hex_color()
    }
    data.update(overrides)
    return data

# --- Category API Tests ---

def test_create_category(client: TestClient, db: Session, auth_headers: dict, faker_instance): # Assuming auth might be added later
    category_data = get_category_create_data(faker_instance)

    response: Response = client.post(
        f"{settings.API_V1_STR}/categories/",
        json=category_data,
        # headers=auth_headers # Uncomment if/when auth is added to this endpoint
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == category_data["name"]
    assert data["slug"] == category_data["slug"]
    assert "id" in data

    # Verify in DB
    category_db = category_service.get(db, id=data["id"])
    assert category_db is not None
    assert category_db.name == category_data["name"]

def test_create_category_duplicate_slug(client: TestClient, db: Session, faker_instance):
    shared_slug = f"unique-cat-slug-{faker_instance.uuid4()[:6]}"
    category_data1 = get_category_create_data(faker_instance, slug=shared_slug, name="First Category with Slug")
    response1: Response = client.post(f"{settings.API_V1_STR}/categories/", json=category_data1)
    assert response1.status_code == 201

    category_data2 = get_category_create_data(faker_instance, slug=shared_slug, name="Second Category with Same Slug")
    response2: Response = client.post(f"{settings.API_V1_STR}/categories/", json=category_data2)
    # The endpoint currently returns 400 for this, as implemented in categories.py
    assert response2.status_code == 400, response2.text
    assert f"Category with slug '{shared_slug}' already exists" in response2.json()["detail"]


def test_create_subcategory(client: TestClient, db: Session, faker_instance):
    parent_category_data = get_category_create_data(faker_instance, name="Parent Category")
    parent_response = client.post(f"{settings.API_V1_STR}/categories/", json=parent_category_data)
    assert parent_response.status_code == 201
    parent_id = parent_response.json()["id"]

    sub_category_data = get_category_create_data(faker_instance, name="Sub Category", parent_id=parent_id)
    sub_response = client.post(f"{settings.API_V1_STR}/categories/", json=sub_category_data)
    assert sub_response.status_code == 201, sub_response.text
    data = sub_response.json()
    assert data["name"] == sub_category_data["name"]
    assert data["parent_id"] == parent_id

    # Verify in DB
    sub_category_db = category_service.get(db, id=data["id"])
    assert sub_category_db is not None
    assert sub_category_db.parent_id == parent_id


def test_read_categories_paginated(client: TestClient, db: Session, faker_instance):
    # Create a few categories
    for i in range(5):
        client.post(
            f"{settings.API_V1_STR}/categories/",
            json=get_category_create_data(faker_instance, name=f"Category Batch {i}")
        )

    response: Response = client.get(f"{settings.API_V1_STR}/categories/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json() # This will be a list of categories
    assert len(data) == 3 # Assuming default listing returns all with subcategories

    # Test topLevelOnly
    # First, ensure at least one subcategory exists for a meaningful test
    parent_cat_data = get_category_create_data(faker_instance, name="Top Parent For Filter")
    parent_resp = client.post(f"{settings.API_V1_STR}/categories/", json=parent_cat_data)
    parent_id = parent_resp.json()["id"]
    client.post(f"{settings.API_V1_STR}/categories/", json=get_category_create_data(faker_instance, name="Child of Top Parent", parent_id=parent_id))

    response_top: Response = client.get(f"{settings.API_V1_STR}/categories/?topLevel=true")
    assert response_top.status_code == 200
    data_top = response_top.json()
    assert len(data_top) > 0 # Should be at least one top-level category
    for cat in data_top:
        assert cat["parent_id"] is None


def test_read_single_category_by_id(client: TestClient, db: Session, faker_instance):
    category_data = get_category_create_data(faker_instance)
    create_response = client.post(f"{settings.API_V1_STR}/categories/", json=category_data)
    category_id = create_response.json()["id"]

    response: Response = client.get(f"{settings.API_V1_STR}/categories/{category_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == category_data["name"]
    assert "subcategories" in data # Endpoint should return subcategories

def test_read_single_category_by_slug(client: TestClient, db: Session, faker_instance):
    category_slug = f"my-specific-cat-slug-{faker_instance.uuid4()[:6]}"
    category_data = get_category_create_data(faker_instance, slug=category_slug)
    create_response = client.post(f"{settings.API_V1_STR}/categories/", json=category_data)
    assert create_response.status_code == 201

    response: Response = client.get(f"{settings.API_V1_STR}/categories/{category_slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == category_slug


def test_read_category_not_found(client: TestClient):
    response: Response = client.get(f"{settings.API_V1_STR}/categories/999999") # Non-existent ID
    assert response.status_code == 404
    response_slug: Response = client.get(f"{settings.API_V1_STR}/categories/non-existent-cat-slug")
    assert response_slug.status_code == 404


def test_update_category(client: TestClient, db: Session, faker_instance):
    category_data = get_category_create_data(faker_instance)
    create_response = client.post(f"{settings.API_V1_STR}/categories/", json=category_data)
    category_id = create_response.json()["id"]

    update_payload = {
        "name": "Updated Category Name",
        "description": "Updated description.",
        "color": "#FF0000"
    }
    response: Response = client.put(
        f"{settings.API_V1_STR}/categories/{category_id}",
        json=update_payload
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated Category Name"
    assert data["description"] == "Updated description."
    assert data["color"] == "#FF0000"
    # Slug should not change unless explicitly provided in update and different
    assert data["slug"] == category_data["slug"]

    category_db = category_service.get(db, id=category_id)
    assert category_db.name == "Updated Category Name"


def test_delete_category(client: TestClient, db: Session, faker_instance):
    category_data = get_category_create_data(faker_instance)
    create_response = client.post(f"{settings.API_V1_STR}/categories/", json=category_data)
    category_id = create_response.json()["id"]

    response: Response = client.delete(f"{settings.API_V1_STR}/categories/{category_id}")
    assert response.status_code == 200, response.text

    category_db = category_service.get(db, id=category_id)
    assert category_db is None

def test_delete_category_with_subcategories_fails(client: TestClient, db: Session, faker_instance):
    parent_data = get_category_create_data(faker_instance, name="Parent To Delete")
    parent_resp = client.post(f"{settings.API_V1_STR}/categories/", json=parent_data)
    parent_id = parent_resp.json()["id"]

    sub_data = get_category_create_data(faker_instance, name="Subcategory Preventing Deletion", parent_id=parent_id)
    client.post(f"{settings.API_V1_STR}/categories/", json=sub_data)

    response: Response = client.delete(f"{settings.API_V1_STR}/categories/{parent_id}")
    assert response.status_code == 400
    assert "Cannot delete category: it has subcategories" in response.json()["detail"]

# Note: Test for deleting category with products would require creating a product associated with the category.
# This is currently commented out in the endpoint, but if implemented, a test should be added.

def test_delete_category_not_found(client: TestClient):
    response: Response = client.delete(f"{settings.API_V1_STR}/categories/88888")
    assert response.status_code == 404
