from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import os
import base64
from PIL import Image, UnidentifiedImageError
import io

from app import schemas
from app.services import product_service, category_service # Assuming category_service exists for validation
from app.db.session import get_db
from app.api import dependencies # For authentication/authorization
from app.models.user import User # To type hint current_user
from app.api.dependencies import get_current_active_user  # Ajusta el path si tu dependencia está en otro módulo
from app.schemas.product_image import ProductImageCreate

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Product,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_current_active_user)] # Example: Require user to be logged in
)
async def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user) # Get the user
):
    """
    Create a new product.
    Requires authentication.
    """
    # Validate category_id
    category = category_service.get(db, id=product_in.category_id)
    if not category:
        raise HTTPException(status_code=400, detail=f"Category with id {product_in.category_id} not found.")

    # Check for SKU uniqueness if your DB doesn't enforce it strictly before commit or if you want early feedback
    # existing_sku_product = product_service.get_by_sku(db, sku=product_in.sku) # Assumes get_by_sku method
    # if existing_sku_product:
    #     raise HTTPException(status_code=400, detail=f"Product with SKU {product_in.sku} already exists.")

    try:
        return product_service.create(db=db, obj_in=product_in, created_by_user_id=current_user.id)
    except Exception as e: # Catch potential IntegrityErrors from slug/sku uniqueness or other DB issues
        # Log e
        raise HTTPException(status_code=400, detail=f"Could not create product. Error: {str(e)}")


@router.get("/", response_model=schemas.ProductPaginated)
async def read_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, alias="page_offset"), # ge=0 means greater than or equal to 0
    limit: int = Query(10, ge=1, le=100, alias="page_limit"), # le=100 means less than or equal to 100
    category_id: Optional[int] = Query(None),
    status_filter: Optional[schemas.ProductStatus] = Query(None, alias="status"), # Use the Literal type
    featured: Optional[bool] = Query(None)
    # Add more filters like search_term, price_min, price_max, etc.
):
    """
    Retrieve a paginated list of products.
    Optionally filter by category_id, status, featured status.
    """
    filters = {
        "category_id": category_id,
        "status": status_filter,
        "featured": featured
    }
    # Remove None filters to avoid passing them to the service if not set
    active_filters = {k: v for k, v in filters.items() if v is not None}

    products, total = product_service.get_multi_paginated(db, skip=skip, limit=limit, filters=active_filters)
    return schemas.ProductPaginated(
        total=total,
        items=products,
        page=(skip // limit) + 1 if limit > 0 else 1, # Calculate current page
        size=limit
    )

@router.get("/{product_id_or_slug}", response_model=schemas.Product)
async def read_product(
    product_id_or_slug: str, # Can be int (ID) or str (slug)
    db: Session = Depends(get_db)
):
    """
    Retrieve a single product by its ID or slug.
    """
    db_product: Optional[schemas.Product] = None
    if product_id_or_slug.isdigit():
        db_product = product_service.get(db, id=int(product_id_or_slug))
    else:
        db_product = product_service.get_product_by_slug(db, slug=product_id_or_slug)

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put(
    "/{product_id}",
    response_model=schemas.Product,
    dependencies=[Depends(dependencies.get_current_active_user)] # Example: Require user to be logged in
)
async def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user) # Get the user
):
    """
    Update an existing product.
    Requires authentication.
    """
    db_product = product_service.get(db, id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_in.category_id:
        category = category_service.get(db, id=product_in.category_id)
        if not category:
            raise HTTPException(status_code=400, detail=f"Category with id {product_in.category_id} not found.")

    # Add more validation as needed (e.g., SKU uniqueness if changed)

    try:
        return product_service.update(db=db, db_obj=db_product, obj_in=product_in, last_modified_by_user_id=current_user.id)
    except Exception as e:
        # Log e
        raise HTTPException(status_code=400, detail=f"Could not update product. Error: {str(e)}")


@router.delete(
    "/{product_id}",
    response_model=schemas.Product,  # O un mensaje de éxito
    dependencies=[Depends(dependencies.get_current_active_user)]
)
async def deactivate_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user) # Ensure user is logged in
):
    """
    Deactivate a product (soft delete).
    Changes product status to 'inactive' instead of deleting from DB.
    """
    product_to_deactivate = product_service.get(db, id=product_id)
    if not product_to_deactivate:
        raise HTTPException(status_code=404, detail="Product not found")

    updated_product = product_service.update(db, db_obj=product_to_deactivate, obj_in={"status": "inactive"})
    return updated_product


# Endpoints for Product Images (example)
@router.delete(
    "/images/{image_id}",
    response_model=schemas.ProductImage,
    dependencies=[Depends(dependencies.get_current_active_user)]
)
async def delete_product_image_from_product(
    image_id: int,
    db: Session = Depends(get_db)
):
    deleted_image = product_service.remove_product_image(db, image_id=image_id)
    if not deleted_image:
        raise HTTPException(status_code=404, detail="Image not found")
    return deleted_image

@router.post("/{product_id}/images", status_code=status.HTTP_201_CREATED, response_model=schemas.ProductImage)
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    is_main: bool = Form(False),
    alt: Optional[str] = Form(None),
    display_order: Optional[int] = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload an image for a product.
    Expects multipart/form-data with 'image' (file), 'is_main' (bool), 'alt' (str, optional), 'display_order' (int, optional).
    """
    product = product_service.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Leer el archivo original
    original_content = await image.read()
    input_stream = io.BytesIO(original_content)
    try:
        img = Image.open(input_stream)
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGB")
        output_stream = io.BytesIO()
        img.save(output_stream, format="JPEG", quality=70)
        compressed_content = output_stream.getvalue()
        image_base64 = base64.b64encode(compressed_content).decode("utf-8")
        mime_type = "image/jpeg"
    except UnidentifiedImageError:
        # Si el formato no es soportado, guarda el archivo original en base64
        image_base64 = base64.b64encode(original_content).decode("utf-8")
        mime_type = image.content_type or "application/octet-stream"
    data_url = f"data:{mime_type};base64,{image_base64}"

    image_in = ProductImageCreate(
        url=data_url,
        alt=alt,
        display_order=display_order,
        is_main=is_main
    )

    db_image = product_service.add_product_image(db, product=product, image_in=image_in)
    return db_image

@router.get("/{product_id}/stock-history", response_model=List[schemas.StockHistory])
async def get_stock_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get stock history for a product.
    """
    product = product_service.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.stock_histories

