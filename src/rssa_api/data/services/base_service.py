"""Base service providing common CRUD operations."""

import uuid
from typing import Any, Generic, TypeVar

import structlog
from pydantic import BaseModel
from rssa_storage.shared import BaseRepository, RepoQueryOptions, merge_repo_query_options

from rssa_api.data.utility import extract_load_strategies

logging = structlog.getLogger('RSSA-BaseService')

ModelType = TypeVar('ModelType')
RepoType = TypeVar('RepoType', bound='BaseRepository')
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class BaseService(Generic[ModelType, RepoType]):
    """Base service providing common CRUD operations."""

    def __init__(self, repo: RepoType):
        """Base service providing common CRUD operations."""
        self.repo = repo

    async def create(self, schema: BaseModel, **extra_fields) -> ModelType:
        """Generic create method."""
        model_data = schema.model_dump(exclude_unset=True)
        model_data.update(extra_fields)
        model_instance = self.repo.model(**model_data)
        return await self.repo.create(model_instance)

    async def get(self, id: uuid.UUID, schema: type[SchemaType], *, options: RepoQueryOptions | None = None) -> Any:
        """Basic get by ID."""
        filter_option = RepoQueryOptions(filters={'id': id})
        if options:
            options = merge_repo_query_options(options, filter_option)
        else:
            options = filter_option
        top_cols, rel_map = extract_load_strategies(schema)
        options.load_columns = top_cols
        options.load_relationships = rel_map

        data_obj = await self.repo.find_one(options)

        if not data_obj:
            return None

        if schema:
            return schema.model_validate(data_obj)

    async def get_all(
        self,
        schema: type[SchemaType],
        *,
        options: RepoQueryOptions | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[SchemaType]:
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

        return [schema.model_validate(obj) for obj in data_objs]

    async def update(self, id: uuid.UUID, update_dict: dict[str, Any]) -> None:
        """Generic update method."""
        await self.repo.update(id, update_dict)

    async def delete(self, id: uuid.UUID) -> None:
        """Generic delete method."""
        await self.repo.delete(id)

    async def count(self, *, options: RepoQueryOptions | None = None) -> int:
        """Generic count, using SEARCHABLE_COLUMNS from repo."""
        options = options or RepoQueryOptions()
        if options.search_text:
            search_cols = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])
            options.search_columns = search_cols

        return await self.repo.count(options)
