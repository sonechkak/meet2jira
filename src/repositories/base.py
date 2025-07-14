from abc import ABC
from pydantic import BaseModel
from typing import Optional, TypeVar, Type, Generic, List, Any, Dict, Union

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from src.database import (
    Base,
    AsyncSessionLocal
)


# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Base repository class for common repository functionality."""

    def __init__(self, model: Type[ModelType], db: AsyncSessionLocal):
        self.model = model
        self.db = db

    async def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record in the database."""

        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get(
            self, id: int, *, load_relationships: bool = False
    ) -> Optional[ModelType]:
        """Get a record by ID."""
        query = select(self.model).where(self.model.id == id)

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_field(
            self,
            field_name: str,
            field_value: Any,
            *,
            load_relationships: bool = False,
    ) -> Optional[ModelType]:
        """Get a record by any field."""
        query = select(self.model).where(getattr(self.model, field_name) == field_value)

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_multi(
            self,
            *,
            skip: int = 0,
            limit: int = 100,
            load_relationships: bool = False,
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        query = select(self.model).offset(skip).limit(limit)

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
            self,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID."""
        db_obj = await self.get(id=id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
        return db_obj

    async def remove(self, id: int) -> Optional[ModelType]:
        """Remove a record by ID (alias for delete)."""
        return await self.delete(id=id)

    async def count(self) -> int:
        """Count total records."""
        query = select(func.count(self.model.id))
        result = await self.db.execute(query)
        return result.scalar()

    async def exists(self, *, id: int) -> bool:
        """Check if a record exists by ID."""
        db_obj = await self.get(id=id)
        return db_obj is not None

    async def bulk_create(self, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in bulk."""
        db_objs = []
        for obj_in in objs_in:
            obj_data = obj_in.model_dump()
            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)

        self.db.add_all(db_objs)
        await self.db.commit()

        for db_obj in db_objs:
            await self.db.refresh(db_obj)

        return db_objs

    async def bulk_update(self, *, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records in bulk."""
        updated_count = 0
        for update_data in updates:
            record_id = update_data.pop("id")
            if update_data:
                query = (
                    update(self.model)
                    .where(self.model.id == record_id)
                    .values(**update_data)
                )
                result = await self.db.execute(query)
                updated_count += result.rowcount

        await self.db.commit()
        return updated_count

    async def bulk_delete(self, *, ids: List[int]) -> int:
        """Delete multiple records in bulk."""
        query = (
            delete(self.model)
            .where(self.model.id.in_(ids))
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount

    async def get_by_field_list(
            self,
            field_name: str,
            field_values: List[Any],
            *,
            load_relationships: bool = False,
    ) -> List[ModelType]:
        """Get records by field values (IN clause)."""
        query = select(self.model).where(
            getattr(self.model, field_name).in_(field_values)
        )

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.options(
                    selectinload(getattr(self.model, relationship.key))
                )

        result = await self.db.execute(query)
        return result.scalars().all()
