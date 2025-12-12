"""Mixin to add 'Next/Previous' navigation logic to any BaseOrderedService."""

import uuid
from typing import Any, Optional, Protocol, TypeVar

from rssa_api.data.models.rssa_base_models import DBBaseOrderedModel
from rssa_api.data.repositories.base_ordered_repo import BaseOrderedRepository

OrderedModelType = TypeVar('OrderedModelType', bound=DBBaseOrderedModel)
OrderedRepoType = TypeVar('OrderedRepoType', bound=BaseOrderedRepository, covariant=True)


class ServiceProtocol(Protocol[OrderedModelType, OrderedRepoType]):
    """Protocol to enforce required attributes/methods for the NavigationMixin.

    Requires:
                1. self.repo (of type BaseOrderedRepository)
                2. self.get() (standard fetch)
    """

    repo: OrderedRepoType

    async def get(self, id: uuid.UUID) -> Optional[OrderedModelType]:
        """Fetch an item by its ID."""
        ...

    async def get_detailed(self, id: uuid.UUID) -> Optional[OrderedModelType]:
        """Fetch an item by its ID with details."""
        ...


class NavigationMixin(ServiceProtocol[OrderedModelType, OrderedRepoType]):
    """Mixin to add 'Next/Previous' navigation logic to any BaseOrderedService.

    Requires the host class to have:
                1. self.repo (of type BaseOrderedRepository)
                2. self.get() (standard fetch)
    """

    async def get_with_navigation(self, current_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """Fetches the current item AND the ID of the next item in the sequence."""
        current_item = await self.get_detailed(current_id)
        if not current_item:
            return None

        next = await self._get_next(current_item)

        return {
            'current': current_item,
            'next_id': next['id'],
            'next_path': next['path'],
        }

    async def get_first_with_navigation(self, parent_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """Fetches the first item under a parent AND the ID of the next item in the sequence."""
        load_options = getattr(self.repo, 'LOAD_FULL_DETAILS', None)
        first_item = await self.repo.get_first_ordered_instance(parent_id, load_options=load_options)
        if not first_item:
            return None

        next = await self._get_next(first_item)

        return {
            'current': first_item,
            'next_id': next['id'],
            'next_path': next['path'],
        }

    async def _get_next(self, current_item: OrderedModelType) -> dict[str, Any]:
        """Helper to get the next item's ID and path if available."""
        next = await self.repo.get_next_ordered_instance(current_item)
        next_id = None
        next_path = None
        if next:
            next_id = next.id
            next_path = getattr(next, 'path', None)

        return {
            'id': next_id,
            'path': next_path,
        }
