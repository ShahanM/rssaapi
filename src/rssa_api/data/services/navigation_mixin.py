"""Mixin to add 'Next/Previous' navigation logic to any BaseOrderedService."""

import uuid
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

# Adjust these imports to match your actual module paths
from rssa_storage.shared.base_ordered_repo import BaseOrderedRepository, OrderedRepoQueryOptions
from rssa_storage.shared.base_repo import RepoQueryOptions
from rssa_storage.shared.db_utils import SharedOrderedModel

from rssa_api.data.utility import extract_load_strategies

OrderedModelType = TypeVar('OrderedModelType', bound=SharedOrderedModel)
OrderedRepoType = TypeVar('OrderedRepoType', bound=BaseOrderedRepository)


class ServiceProtocol(Protocol[OrderedModelType, OrderedRepoType]):
    """Protocol to enforce required attributes/methods for the NavigationMixin.

    Because the Mixin now builds queries dynamically, it only requires the repository!
    We no longer need to enforce get() or get_detailed().
    """

    repo: OrderedRepoType


class NavigationMixin(ServiceProtocol[OrderedModelType, OrderedRepoType]):
    """Mixin to add 'Next/Previous' navigation logic to any BaseOrderedService."""

    async def get_with_navigation(self, current_id: uuid.UUID, schema: type[BaseModel]) -> dict[str, Any] | None:
        """Fetches the current item dynamically based on the schema AND the next item."""
        top_cols, rel_map = extract_load_strategies(schema)

        required_cols = {'id', 'order_position', self.repo.parent_id_column_name}
        top_cols = list(set(top_cols).union(required_cols))

        options = RepoQueryOptions(filters={'id': current_id}, load_columns=top_cols, load_relationships=rel_map)

        current_model = await self.repo.find_one(options)
        if not current_model:
            return None

        next_info = await self._get_next(current_model)

        return {
            'current': schema.model_validate(current_model),  # Validate into the requested schema
            'next_id': next_info['id'],
            'next_path': next_info['path'],
        }

    async def get_first_with_navigation(self, parent_id: uuid.UUID, schema: type[BaseModel]) -> dict[str, Any] | None:
        """Fetches the first item dynamically AND the next item in the sequence."""
        top_cols, rel_map = extract_load_strategies(schema)

        required_cols = {'id', 'order_position', self.repo.parent_id_column_name}
        top_cols = list(set(top_cols).union(required_cols))

        options = OrderedRepoQueryOptions(
            filters={self.repo.parent_id_column_name: parent_id},
            sort_by='order_position',
            sort_desc=False,
            limit=1,
            load_columns=top_cols,
            load_relationships=rel_map,
        )

        first_model = await self.repo.find_one(options)
        if not first_model:
            return None

        next_info = await self._get_next(first_model)

        return {
            'current': schema.model_validate(first_model),
            'next_id': next_info['id'],
            'next_path': next_info['path'],
        }

    async def _get_next(self, current_item: OrderedModelType) -> dict[str, Any]:
        """Helper to get the next item's ID and path if available."""
        next_model = await self.repo.get_next_ordered_instance(current_item)

        next_id = None
        next_path = None
        if next_model:
            next_id = next_model.id
            next_path = getattr(next_model, 'path', None)

        return {
            'id': next_id,
            'path': next_path,
        }
