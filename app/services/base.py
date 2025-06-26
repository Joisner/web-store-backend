from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return (
            db.query(self.model)
            .order_by(self.model.id)  # Asegura el order_by para MSSQL
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_paginated(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> (List[ModelType], int):
        total = db.query(self.model).count()
        items = db.query(self.model).offset(skip).limit(limit).all()
        return items, total

    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        # Add any additional kwargs passed to the create method, e.g. user_id
        db_obj = self.model(**obj_in_data, **kwargs)
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            # You might want to raise a custom exception here or handle it specifically
            # For example, if a unique constraint is violated
            raise e
        except Exception as e:
            db.rollback()
            raise e


    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) # Pydantic v2
            # update_data = obj_in.dict(exclude_unset=True) # Pydantic v1

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise e

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        obj = db.query(self.model).get(id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                db.rollback()
                raise e
        return None # Or raise an exception if object not found

    def remove_obj(self, db: Session, *, db_obj: ModelType) -> ModelType:
        try:
            db.delete(db_obj)
            db.commit()
            return db_obj
        except Exception as e:
            db.rollback()
            raise e

# Example of how to use it:
# from app.models.user import User
# from app.schemas.user import UserCreate, UserUpdate
# user_service = CRUDBase[User, UserCreate, UserUpdate](User)
