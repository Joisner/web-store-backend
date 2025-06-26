from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas
from app.services import category_service
from app.db.session import get_db
from app.api import dependencies # For authentication if needed for create/update/delete
from app.models.user import User # To type hint current_user
from fastapi import Query
router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Category,
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(dependencies.get_current_active_user)] # Uncomment if auth is needed
)
async def create_category(
    category_in: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(dependencies.get_current_active_user) # Uncomment if auth is needed
):
    """
    Create a new category.
    (Add authentication if category creation should be restricted)
    """
    if category_in.parent_id:
        parent_category = category_service.get(db, id=category_in.parent_id)
        if not parent_category:
            raise HTTPException(status_code=400, detail=f"Parent category with id {category_in.parent_id} not found.")

    # Check for slug uniqueness
    existing_slug_category = category_service.get_by_slug(db, slug=category_in.slug)
    if existing_slug_category:
        raise HTTPException(status_code=400, detail=f"Category with slug '{category_in.slug}' already exists.")

    try:
        return category_service.create(db=db, obj_in=category_in)
    except Exception as e:
        # Log e
        raise HTTPException(status_code=400, detail=f"Could not create category. Error: {str(e)}")


@router.get("/", response_model=List[schemas.Category])
async def read_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    top_level_only: bool = Query(False, alias="topLevel") # Query param to get only top-level categories
):
    """
    Retrieve a list of categories.
    Set top_level_only=true to get only categories without a parent.
    Includes subcategories recursively.
    """
    if top_level_only:
        categories = category_service.get_top_level_categories(db)
    else:
        categories = category_service.get_multi(db, skip=skip, limit=limit)
    return categories


@router.get("/{category_id_or_slug}", response_model=schemas.Category)
async def read_category(
    category_id_or_slug: str, # Can be int (ID) or str (slug)
    db: Session = Depends(get_db)
):
    """
    Retrieve a single category by its ID or slug.
    Includes subcategories recursively.
    """
    db_category: Optional[schemas.Category] = None
    if category_id_or_slug.isdigit():
        db_category = category_service.get(db, id=int(category_id_or_slug))
    else:
        db_category = category_service.get_by_slug(db, slug=category_id_or_slug)

    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.put(
    "/{category_id}",
    response_model=schemas.Category,
    # dependencies=[Depends(dependencies.get_current_active_user)] # Uncomment if auth is needed
)
async def update_category(
    category_id: int,
    category_in: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(dependencies.get_current_active_user) # Uncomment if auth is needed
):
    """
    Update an existing category.
    (Add authentication if category updates should be restricted)
    """
    db_category = category_service.get(db, id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category_in.parent_id and category_in.parent_id != db_category.parent_id:
        if category_in.parent_id == category_id: # Prevent self-parenting
             raise HTTPException(status_code=400, detail="Category cannot be its own parent.")
        parent_category = category_service.get(db, id=category_in.parent_id)
        if not parent_category:
            raise HTTPException(status_code=400, detail=f"New parent category with id {category_in.parent_id} not found.")

    if category_in.slug and category_in.slug != db_category.slug:
        existing_slug_category = category_service.get_by_slug(db, slug=category_in.slug)
        if existing_slug_category and existing_slug_category.id != category_id:
            raise HTTPException(status_code=400, detail=f"Category with slug '{category_in.slug}' already exists.")

    try:
        return category_service.update(db=db, db_obj=db_category, obj_in=category_in)
    except Exception as e:
        # Log e
        raise HTTPException(status_code=400, detail=f"Could not update category. Error: {str(e)}")


@router.delete(
    "/{category_id}",
    response_model=schemas.Category,  # O un mensaje de éxito
    dependencies=[Depends(dependencies.get_current_active_user)]
)
async def deactivate_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(dependencies.get_current_active_user)
):
    """
    Deactivate a category (soft delete).
    Changes category status to 'inactive' instead of deleting from DB.
    """
    category_to_deactivate = category_service.get(db, id=category_id)
    if not category_to_deactivate:
        raise HTTPException(status_code=404, detail="Category not found")

    updated_category = category_service.update(db, db_obj=category_to_deactivate, obj_in={"status": "inactive"})
    return updated_category
