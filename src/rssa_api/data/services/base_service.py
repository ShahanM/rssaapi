"""Base service providing common CRUD operations."""

import uuid
from typing import Any, Generic, TypeVar, overload

from pydantic import BaseModel
from rssa_storage.shared import BaseRepository, RepoQueryOptions, merge_repo_query_options

from rssa_api.data.utility import extract_load_strategies

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
    async def get(
        self, id: uuid.UUID, schema: type[SchemaType], *, options: RepoQueryOptions | None = None
    ) -> SchemaType | None: ...

    @overload
    async def get(
        self, id: uuid.UUID, schema: None = None, *, options: RepoQueryOptions | None = None
    ) -> ModelType | None: ...

    async def get(
        self, id: uuid.UUID, schema: type[SchemaType] | None = None, *, options: RepoQueryOptions | None = None
    ) -> Any:
        """Basic get by ID.

        Args:
            id: The unique identifier of the model instance.
            schema: Optional Pydantic schema to validate the result against.
            options: Optional query options for additional criteria.

        Returns:
            The model instance or validated schema, or None if not found.
        """
        filter_option = RepoQueryOptions(filters={'id': id})
        if options:
            options = merge_repo_query_options(options, filter_option)
        else:
            options = filter_option
        top_cols, rel_map = extract_load_strategies(schema) if schema else (None, None)
        options.load_columns = top_cols
        options.load_relationships = rel_map

        data_obj = await self.repo.find_one(options)

        if not data_obj:
            return None

        if schema:
            return schema.model_validate(data_obj)
        return data_obj

    @overload
    async def get_all(self, schema: type[SchemaType], *, options: RepoQueryOptions) -> list[SchemaType]: ...

    @overload
    async def get_all(
        self,
        schema: type[SchemaType],
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[SchemaType]: ...

    @overload
    async def get_all(self, schema: None = None, *, options: RepoQueryOptions) -> list[ModelType]: ...

    @overload
    async def get_all(
        self,
        schema: None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[ModelType]: ...

    async def get_all(
        self,
        schema: type[SchemaType] | None = None,
        *,
        options: RepoQueryOptions | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[Any]:
        """Generic fetch all."""
        if options is None:
            options = RepoQueryOptions()

        if limit is not None:
            options.limit = limit
        if offset is not None:
            options.offset = offset
        if sort_by is not None:
            options.sort_by = sort_by
        if sort_dir is not None:
            options.sort_desc = sort_dir == 'desc'
        if search is not None:
            options.search_text = search

        options.search_columns = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])
        top_cols, rel_map = extract_load_strategies(schema) if schema else (None, None)

        if top_cols:
            options.load_columns = top_cols
        if rel_map:
            options.load_relationships = rel_map

        data_objs = await self.repo.find_many(options)

        if schema:
            return [schema.model_validate(obj) for obj in data_objs]
        return list(data_objs)

    async def update(self, id: uuid.UUID, update_dict: dict[str, Any]) -> None:
        """Generic update method.

        Args:
            id: The unique identifier of the model instance to update.
            update_dict: A dictionary of fields to update.

        Returns:1
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

    async def count(self, search: str | None = None) -> int:
        """Generic count, using SEARCHABLE_COLUMNS from repo.

        Args:
            search: Optional search string to filter the count.

        Returns:
            The count of items matching the criteria.
        """
        search_cols = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])
        options = RepoQueryOptions(search_text=search, search_columns=search_cols)
        return await self.repo.count(options)
