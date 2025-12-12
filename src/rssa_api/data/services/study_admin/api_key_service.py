"""Service that manages application API keys.

The ApiKeyService class is used to manage the API key to register and
authenticate frontend study applications.
"""

import secrets
import uuid
from typing import Optional, Sequence

from async_lru import alru_cache
from cryptography.fernet import Fernet

from rssa_api.config import get_env_var
from rssa_api.data.models.study_components import ApiKey
from rssa_api.data.repositories.study_admin import ApiKeyRepository
from rssa_api.data.schemas.study_components import ApiKeyRead
from rssa_api.data.utility import sa_obj_to_dict

ENCRYPTION_KEY = get_env_var('RSSA_MASTER_ENCRYPTION_KEY')


class ApiKeyService:
    """Service for managing API keys for studies.

    This service handles the creation, validation, and retrieval of API keys.
    Keys are encrypted using Fernet symmetric encryption.
    """

    def __init__(self, api_key_repo: ApiKeyRepository):
        """Initializes the ApiKeyService.

        Args:
            api_key_repo: The repository for API key data access.
        """
        self.repo = api_key_repo

    def generate_key_and_hash(self) -> tuple[str, str]:
        """Generate a secure random API key and its encrypted version.

        Returns:
            A tuple containing the plain-text API key and the Fernet-encrypted key as a string.
        """
        plain_text_key = secrets.token_urlsafe(32)
        fernet = Fernet(ENCRYPTION_KEY.encode())
        encrypted_bytes = fernet.encrypt(plain_text_key.encode())
        encrypted_str = encrypted_bytes.decode('utf-8')
        # key_hash = hashlib.sha256(plain_text_key.encode()).hexdigest()

        return plain_text_key, encrypted_str

    async def create_api_key_for_study(
        self,
        study_id: uuid.UUID,
        description: str,
        user_id: uuid.UUID,
    ) -> ApiKeyRead:
        """Creates and saves a new API key for a study.

        This will invalidate any existing active keys for the same study and user.

        Args:
            study_id: The ID of the study to associate the key with.
            description: A description for the API key.
            user_id: The ID of the user creating the key.

        Returns:
            An ApiKeyRead object including the new plain-text key.
        """
        _plain_key, key_hash = self.generate_key_and_hash()
        # current_active_keys = await self.repo.get_all_by_fields(
        #     [('study_id', study_id), ('user_id', user_id), ('is_active', True)]
        # )
        from rssa_api.data.repositories.base_repo import RepoQueryOptions
        repo_options = RepoQueryOptions(
            filters={'study_id': study_id, 'user_id': user_id, 'is_active': True}
        )
        current_active_keys = await self.repo.find_many(repo_options)
        await self._invalidate_keys(current_active_keys)

        new_api_key = ApiKey(
            key_hash=key_hash,
            description=description,
            study_id=study_id,
            user_id=user_id,
        )

        await self.repo.create(new_api_key)
        api_key_dict = sa_obj_to_dict(new_api_key)
        api_key_dict['plain_text_key'] = _plain_key

        return ApiKeyRead.model_validate(api_key_dict)

    async def _invalidate_keys(self, api_keys: Sequence[ApiKey]) -> None:
        """Sets a sequence of API keys to be inactive.

        Args:
            api_keys: A sequence of ApiKey model objects to invalidate.
        """
        for api_key in api_keys:
            if api_key.is_active:
                await self.repo.update(api_key.id, {'is_active': False})

    async def get_api_keys_for_study(
        self,
        study_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ApiKeyRead]:
        """Retrieves all API keys for a given study and user.

        The plain-text version of the key is decrypted and included in the result.

        Args:
            study_id: The ID of the study.
            user_id: The ID of the user.

        Returns:
            A list of ApiKeyRead objects, each including the plain-text key.
        """
        # api_keys = await self.repo.get_all_by_fields([('study_id', study_id), ('user_id', user_id)])
        from rssa_api.data.repositories.base_repo import RepoQueryOptions
        repo_options = RepoQueryOptions(filters={'study_id': study_id, 'user_id': user_id})
        api_keys = await self.repo.find_many(repo_options)
        
        api_key_dicts = []
        if api_keys:
            fernet = Fernet(ENCRYPTION_KEY.encode())
            for api_key in api_keys:
                encrypted_bytes = api_key.key_hash.encode('utf-8')
                decrypted_bytes = fernet.decrypt(encrypted_bytes)
                plain_text_key = decrypted_bytes.decode()
                api_key_dicts.append(
                    {
                        'id': api_key.id,
                        'study_id': api_key.study_id,
                        'user_id': api_key.user_id,
                        'is_active': api_key.is_active,
                        'created_at': api_key.created_at,
                        'last_used_at': api_key.last_used_at,
                        'description': api_key.description,
                        'plain_text_key': plain_text_key,
                    }
                )

        return [ApiKeyRead.model_validate(api_key) for api_key in api_key_dicts]

    @alru_cache(maxsize=128)
    async def validate_api_key(self, api_key_id: uuid.UUID, api_key_secret: str) -> Optional[ApiKey]:
        """Validate API key against a provided key secret.

        This method looks up an api_key from the database using the provided key id.
        If a key is found, it is decrypts a Fernet encrypted key and then compares it
        with the key secret.

        Args:
            api_key_id: The API key id to lookup.
            api_key_secret: The api key secret to use for validation.

        Returns:
            The valid API Key if it is found, otherwise None.

        """
        # key_record = await self.repo.get(api_key_id)
        from rssa_api.data.repositories.base_repo import RepoQueryOptions
        key_record = await self.repo.find_one(RepoQueryOptions(filters={'id': api_key_id}))
        if not key_record:
            return None

        try:
            fernet = Fernet(ENCRYPTION_KEY.encode())
            decrypted_secret = fernet.decrypt(key_record.key_hash.encode()).decode()
            if not secrets.compare_digest(decrypted_secret, api_key_secret):
                return None
        except Exception:
            return None

        return key_record
