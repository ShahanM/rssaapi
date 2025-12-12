"""Base service providing common CRUD operations."""

import uuid
from typing import Any, Generic, Optional, Type, TypeVar, overload

from pydantic import BaseModel

from rssa_api.data.repositories.base_repo import BaseRepository, RepoQueryOptions

ModelType = TypeVar('ModelType')
RepoType = TypeVar('RepoType', bound='BaseRepository')
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class BaseService(Generic[ModelType, RepoType]):
    """Base service providing common CRUD operations."""

    def __init__(self, repo: RepoType):
        """Base service providing common CRUD operations."""
        self.repo = repo

    async def create(self, schema: BaseModel, **extra_fields) -> ModelType:
        """Generic create method.

        Args:
            schema: Pydantic schema to create the model from.
            **extra_fields: Additional fields to set on the model.

        Returns:
            The created model instance.
        """
        model_data = schema.model_dump(exclude_unset=True)
        model_data.update(extra_fields)
        model_instance = self.repo.model(**model_data)
        return await self.repo.create(model_instance)

    @overload
    async def get(self, id: uuid.UUID, schema: Type[SchemaType]) -> Optional[SchemaType]: ...

    @overload
    async def get(self, id: uuid.UUID, schema: None = None) -> Optional[ModelType]: ...

    async def get(
        self,
        id: uuid.UUID,
        schema: Optional[Type[SchemaType]] = None,
    ) -> Any:
        """Basic get by ID.

        Args:
            id: The unique identifier of the model instance.
            schema: Optional Pydantic schema to validate the result against.

        Returns:
            The model instance or validated schema, or None if not found.
        """
        # data_obj = await self.repo.get(id)
        data_obj = await self.repo.find_one(RepoQueryOptions(filters={'id': id}))

        if not data_obj:
            return None

        if schema:
            return schema.model_validate(data_obj)
        return data_obj

    @overload
    async def get_detailed(self, id: uuid.UUID, schema: Type[SchemaType]) -> Optional[SchemaType]: ...

    @overload
    async def get_detailed(self, id: uuid.UUID, schema: None = None) -> Optional[ModelType]: ...

    async def get_detailed(self, id: uuid.UUID, schema: Optional[Type[SchemaType]] = None) -> Any:
        """Get by ID, using the Repository's LOAD_FULL_DETAILS configuration if it exists.

        Args:
            id: The unique identifier of the model instance.
            schema: Optional Pydantic schema to validate the result against.

        Returns:
            The model instance with full details, or None if not found.
        """
        options = getattr(self.repo, 'LOAD_FULL_DETAILS', [])
        # data_obj = await self.repo.get(id, options=options)
        data_obj = await self.repo.find_one(RepoQueryOptions(filters={'id': id}, load_options=options))

        if not data_obj:
            return None

        if schema:
            return schema.model_validate(data_obj)

        return data_obj

    async def update(self, id: uuid.UUID, update_dict: dict[str, Any]) -> None:
        """Generic update method.

        Args:
            id: The unique identifier of the model instance to update.
            update_dict: A dictionary of fields to update.

        Returns:
            None
        """
        await self.repo.update(id, update_dict)

    async def delete(self, id: uuid.UUID) -> None:
        """Generic delete method.

        Args:
            id: The unique identifier of the model instance to delete.

        Returns:
            None
        """
        await self.repo.delete(id)

    @overload
    async def get_paged_list(
        self,
        limit: int,
        offset: int,
        schema: Type[SchemaType],
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[SchemaType]: ...

    @overload
    async def get_paged_list(
        self,
        limit: int,
        offset: int,
        schema: None = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[ModelType]: ...

    async def get_paged_list(
        self,
        limit: int,
        offset: int,
        schema: Optional[type[SchemaType]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[Any]:
        """Generic paged list fetcher.

        Automatically uses SEARCHABLE_COLUMNS from the repository.

        Args:
            limit: Number of items to fetch.
            offset: Offset to start fetching from.
            schema: Pydantic schema to validate the results against.
            sort_by: Optional column to sort by.
            sort_dir: Optional sort direction ('asc' or 'desc').
            search: Optional search string to filter results.

        Returns:
            A list of validated schema instances.
        """
        search_cols = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])

        repo_options = RepoQueryOptions(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=(sort_dir == 'desc') if sort_dir else False,
            search_text=search,
            search_columns=search_cols,
        )
        data_objs = await self.repo.find_many(repo_options)

        if schema:
            return [schema.model_validate(obj) for obj in data_objs]
        return data_objs

    async def count(self, search: Optional[str] = None) -> int:
        """Generic count, using SEARCHABLE_COLUMNS from repo.

        Args:
            search: Optional search string to filter the count.

        Returns:
            The count of items matching the criteria.
        """
        search_cols = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])
        return await self.repo.count(filter_str=search, filter_cols=search_cols)
