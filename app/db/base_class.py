from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    id: int
    __name__: str

    # # Generate __tablename__ automatically - SQLAlchemy 2.0 style might not need this as often
    # # For explicit table names, define __tablename__ in each model.
    # # If you still want automatic table names based on class names:
    # from sqlalchemy.ext.declarative import declared_attr
    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return cls.__name__.lower() + "s"
    pass
