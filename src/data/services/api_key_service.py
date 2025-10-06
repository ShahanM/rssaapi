import secrets
import uuid
from typing import Optional, Sequence

from async_lru import alru_cache
from cryptography.fernet import Fernet

from config import get_env_var
from data.models.study_components import ApiKey
from data.repositories import ApiKeyRepository
from data.schemas.study_components import ApiKeySchema
from data.utility import sa_obj_to_dict

ENCRYPTION_KEY = get_env_var('RSSA_MASTER_ENCRYPTION_KEY')


class ApiKeyService:
    def __init__(self, api_key_repo: ApiKeyRepository):
        self.repo = api_key_repo

    def generate_key_and_hash(self) -> tuple[str, str]:
        """Generate a secure random API key and its SHA-256 hash."""
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
    ) -> ApiKeySchema:
        """Creates and saves a new API key for a study."""
        _plain_key, key_hash = self.generate_key_and_hash()
        current_active_keys = await self.repo.get_all_by_fields(
            [('study_id', study_id), ('user_id', user_id), ('is_active', True)]
        )
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

        return ApiKeySchema.model_validate(api_key_dict)

    async def _invalidate_keys(self, api_keys: Sequence[ApiKey]) -> None:
        for api_key in api_keys:
            if api_key.is_active:
                await self.repo.update(api_key.id, {'is_active': False})

    async def get_api_keys_for_study(
        self,
        study_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ApiKeySchema]:
        api_keys = await self.repo.get_all_by_fields([('study_id', study_id), ('user_id', user_id)])
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

        return [ApiKeySchema.model_validate(api_key) for api_key in api_key_dicts]

    @alru_cache(maxsize=128)
    async def validate_api_key(self, api_key_id: uuid.UUID, api_key_secret: str) -> Optional[ApiKey]:
        key_record = await self.repo.get(api_key_id)
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
