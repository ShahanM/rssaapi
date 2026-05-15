"""Service that manages application API keys.

The ApiKeyService class is used to manage the API key to register and
authenticate frontend study applications.
"""

import math
import random
import secrets
import uuid
from collections.abc import Sequence

from async_lru import alru_cache
from cryptography.fernet import Fernet
from rssa_storage.rssadb.models.participant_movie_sequence import PreShuffledMovieList
from rssa_storage.rssadb.models.study_components import ApiKey, User
from rssa_storage.rssadb.repositories.study_admin import ApiKeyRepository, PreShuffledMovieRepository, UserRepository
from rssa_storage.shared import RepoQueryOptions
from sqlalchemy import func, select

from rssa_api.core.config import get_env_var
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.study_components import ApiKeyCreate, ApiKeyRead
from rssa_api.data.services.base_service import BaseService
from rssa_api.data.utility import sa_obj_to_dict

ENCRYPTION_KEY = get_env_var('RSSA_MASTER_ENCRYPTION_KEY')


class ApiKeyService(BaseService[ApiKey, ApiKeyRepository]):
    """Service for managing API keys for studies.

    This service handles the creation, validation, and retrieval of API keys.
    Keys are encrypted using Fernet symmetric encryption.
    """

    def _generate_key_and_hash(self) -> tuple[str, str]:
        """Generate a secure random API key and its encrypted version.

        Returns:
            A tuple containing the plain-text API key and the Fernet-encrypted key as a string.
        """
        plain_text_key = secrets.token_urlsafe(32)
        fernet = Fernet(ENCRYPTION_KEY.encode())
        encrypted_bytes = fernet.encrypt(plain_text_key.encode())
        encrypted_str = encrypted_bytes.decode('utf-8')

        return plain_text_key, encrypted_str

    async def generate_new_api_key(self, apikey_create: ApiKeyCreate) -> ApiKeyRead:
        """Creates and saves a new API key for a study.

        This will invalidate any existing active keys for the same study and user.

        Args:
            apikey_create: model schema consisting of a description, user_id, and study_id.

        Returns:
            An ApiKeyRead object including the new plain-text key.
        """
        _plain_key, key_hash = self._generate_key_and_hash()

        repo_options = RepoQueryOptions(
            filters={'study_id': apikey_create.study_id, 'user_id': apikey_create.user_id, 'is_active': True}
        )
        current_active_keys = await self.repo.find_many(repo_options)
        await self._invalidate_keys(current_active_keys)

        new_api_key = ApiKey(key_hash=key_hash, **apikey_create.model_dump())

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
    async def validate_api_key(self, api_key_id: uuid.UUID, api_key_secret: str) -> ApiKey | None:
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
        key_record = await self.repo.find_one(
            RepoQueryOptions(filters={'id': api_key_id}, load_columns=['id', 'key_hash', 'study_id', 'user_id'])
        )
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


class PreShuffledMovieService(BaseService[PreShuffledMovieList, PreShuffledMovieRepository]):
    """Service for managing pre-shuffled movie lists."""

    async def create_pre_shuffled_movie_list(
        self,
        movie_data: list[dict],
        subset_desc: str,
        seed: int,
        config_payload: dict,
    ) -> None:
        """Create a pre-shuffled movie list."""
        local_rng = random.Random(seed)

        strategy = config_payload.get('strategy', 'Random')
        if strategy == 'A-Res':
            sorted_movies = self._sort_weight_with_a_res(movie_data, local_rng)
            shuffled_ids = [m_id for _, m_id in sorted_movies]
        elif strategy == 'Stratified Chunking RC':
            sorted_movies = sorted(movie_data, key=lambda x: x['rate_count'])
            shuffled_ids = self._shuffle_incremental_stratified_chunking(
                sorted_movies,
                config_payload.get('page_size', 18),
                config_payload.get('popular_threshold', 0.15),
                config_payload.get('popular_per_page', 0.05),
                config_payload.get('popular_growth_rate', 0.20),
                config_payload.get('initial_popular_schedue', [0, 0]),
                rng=local_rng,
            )
        elif strategy == 'Stratified Chunking AvgRatingLD':
            sorted_movies = sorted(
                movie_data, key=lambda x: x.get('average_rating', 0) * math.log1p(x.get('rate_count', 0))
            )  # Score = average_rating * ln(1 + rate_count)
            shuffled_ids = self._shuffle_incremental_stratified_chunking(
                sorted_movies,
                config_payload.get('page_size', 18),
                config_payload.get('popular_threshold', 0.15),
                config_payload.get('popular_per_page', 0.05),
                config_payload.get('popular_growth_rate', 0.20),
                config_payload.get('initial_popular_schedue', [0, 0]),
                rng=local_rng,
            )
        elif strategy == 'Stratified Chunking AvgRatingBA':
            sorted_movies = self._sort_with_bayesian_average(
                movie_data,
                temporal_discounting=config_payload.get('temporal_discounting', True),
                base_year=config_payload.get('base_year', 1985),
                decay_rate=config_payload.get('decay_rate', 0.90),
            )
            stratify_w_genre = config_payload.get('include_genre_in_stratification', True)
            if stratify_w_genre:
                shuffled_ids = self._shuffle_stratified_chunking_with_genres(
                    sorted_movies,
                    config_payload.get('page_size', 18),
                    config_payload.get('popular_threshold', 0.15),
                    config_payload.get('popular_per_page', 0.05),
                    config_payload.get('genre_bucket_size', 36),
                    config_payload.get('active_anchor_limit', 60),
                    config_payload.get('genre_repr_per_page', 0.10),
                    local_rng,
                )
            else:
                shuffled_ids = self._shuffle_incremental_stratified_chunking(
                    sorted_movies,
                    config_payload.get('page_size', 18),
                    config_payload.get('popular_threshold', 0.15),
                    config_payload.get('popular_per_page', 0.05),
                    config_payload.get('popular_growth_rate', 0.20),
                    config_payload.get('initial_popular_schedue', [0, 0]),
                    rng=local_rng,
                )
        else:
            shuffled_ids = [datum['id'] for datum in movie_data]  # Copy to avoid mutating original
            local_rng.shuffle(shuffled_ids)

        preshuffled_list = PreShuffledMovieList(
            subset_desc=subset_desc, seed=seed, movie_ids=shuffled_ids, **config_payload
        )

        await self.repo.create(preshuffled_list)

    def _shuffle_incremental_stratified_chunking(
        self,
        sorted_movies: list[dict],
        page_size: int,
        popular_threshold: float,
        popular_per_page: float,
        popular_growth_rate: float,
        initial_popular_schedue: list[int],
        rng,
    ) -> list[uuid.UUID]:
        split_idx = int(len(sorted_movies) * (1 - popular_threshold))

        obscure_bucket = [m['id'] for m in sorted_movies[:split_idx]]
        popular_bucket = [m['id'] for m in sorted_movies[split_idx:]]

        rng.shuffle(obscure_bucket)
        rng.shuffle(popular_bucket)

        max_popular_per_page = int(page_size * popular_per_page)

        step_size = max(1, int(page_size * popular_growth_rate))

        popular_schedule = [0, 0]
        if initial_popular_schedue is not None:
            popular_schedule = initial_popular_schedue
        current_pop = step_size
        while current_pop < max_popular_per_page:
            popular_schedule.append(current_pop)
            current_pop += step_size

        shuffled_ids = []
        page_num = 0

        while obscure_bucket or popular_bucket:
            if page_num < len(popular_schedule):
                target_pop = popular_schedule[page_num]
            else:
                target_pop = max_popular_per_page

            actual_pop = min(target_pop, len(popular_bucket))
            actual_obs = min(page_size - actual_pop, len(obscure_bucket))

            if actual_obs < (page_size - actual_pop):
                actual_pop = min(page_size - actual_obs, len(popular_bucket))

            page_items = []
            for _ in range(actual_obs):
                page_items.append(obscure_bucket.pop())
            for _ in range(actual_pop):
                page_items.append(popular_bucket.pop())

            rng.shuffle(page_items)

            shuffled_ids.extend(page_items)
            page_num += 1
        return shuffled_ids

    def _shuffle_stratified_chunking_with_genres(
        self,
        sorted_movies: list[dict],
        page_size: int,
        popular_threshold: float,  # Top 15%
        popular_per_page: float,
        genre_bucket_size: int,  # this is only for the candidate pool
        active_anchor_limit: int,
        genre_repr_per_page: float,
        rng,
    ) -> list[uuid.UUID]:
        split_idx = int(len(sorted_movies) * popular_threshold)

        raw_popular = sorted_movies[split_idx:]
        obscure_bucket = [m['id'] for m in sorted_movies[:split_idx]]

        genre_anchors = {}
        general_popular = []

        for movie in reversed(raw_popular):
            genres = movie.get('genres', ['Unknown'])
            if isinstance(genres, str):
                genres = genres.split('|')

            rng.shuffle(genres)

            is_anchor = False
            for g in genres:
                if g not in genre_anchors:
                    genre_anchors[g] = []

                if len(genre_anchors[g]) < genre_bucket_size:
                    genre_anchors[g].append(movie['id'])
                    is_anchor = True
                    break

            if not is_anchor:
                general_popular.append(movie['id'])

        anchor_bucket, unused_candidates = self._shuffle_group_members(genre_anchors, active_anchor_limit, rng)
        general_popular.extend(unused_candidates)
        rng.shuffle(general_popular)
        rng.shuffle(obscure_bucket)

        return self._generate_shuffled_ids_from_buckets(
            page_size,
            anchor_bucket,
            general_popular,
            obscure_bucket,
            popular_per_page,
            genre_repr_per_page,
            rng,
        )

    def _shuffle_group_members(
        self, groups: dict[str, list], active_anchor_limit: int, rng
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        # Shuffle collection within each group
        active_groups = list(groups.keys())
        rng.shuffle(active_groups)

        unused_candidates = []
        group_anchors: dict[str, list] = {}
        for g in active_groups:
            rng.shuffle(groups[g])

            unused_anchors = groups[g][active_anchor_limit:]
            unused_candidates.extend(unused_anchors)
            group_anchors[g] = groups[g][:active_anchor_limit]

        # Use Round-Robin to pick to interleave group representation
        anchor_bucket = []
        while active_groups:
            for g in list(active_groups):
                if group_anchors[g]:
                    anchor_bucket.append(group_anchors[g].pop())
                else:
                    active_groups.remove(g)

        return (anchor_bucket, unused_candidates)

    def _generate_shuffled_ids_from_buckets(
        self,
        page_size,
        anchor_bucket: list[uuid.UUID],
        general_popular: list[uuid.UUID],
        obscure_bucket: list[uuid.UUID],
        popular_per_page: float,
        genre_repr_per_page: float,
        rng,
    ) -> list[uuid.UUID]:
        target_anchors = max(1, int(page_size * genre_repr_per_page))
        target_general = max(1, int(page_size * popular_per_page))

        shuffled_ids = []

        while obscure_bucket or anchor_bucket or general_popular:
            page_items = []

            actual_anchors = min(target_anchors, len(anchor_bucket))
            for _ in range(actual_anchors):
                page_items.append(anchor_bucket.pop())

            actual_general = min(target_general, len(general_popular))
            for _ in range(actual_general):
                page_items.append(general_popular.pop())

            remaining_slots = page_size - len(page_items)
            actual_obscure = min(remaining_slots, len(obscure_bucket))
            for _ in range(actual_obscure):
                page_items.append(obscure_bucket.pop())

            backfill_slots = page_size - len(page_items)
            while backfill_slots > 0 and general_popular:
                page_items.append(general_popular.pop())
                backfill_slots -= 1

            rng.shuffle(page_items)
            shuffled_ids.extend(page_items)

        return shuffled_ids

    def _sort_with_bayesian_average(
        self, movie_data: list[dict], *, temporal_discounting: bool, base_year: int, decay_rate: float = 0.95
    ) -> list[dict]:
        C = sum(m.get('average_rating', 0) for m in movie_data) / len(movie_data)  # dataset prior
        m = sum(m.get('rate_count', 0) for m in movie_data) / len(movie_data)  # stabilizing prior

        def bayesian_score(movie):
            v = movie.get('rate_count', 0)
            R = movie.get('average_rating', 0)

            if (v + m) == 0:
                return 0

            base_score = (v / (v + m)) * R + (m / (v + m)) * C

            if temporal_discounting:
                try:
                    year = int(movie.get('year', base_year))
                except (ValueError, TypeError):
                    year = base_year

                if year < base_year:
                    years_old = base_year - year
                    decay_factor = math.pow(decay_rate, years_old)
                    return base_score * decay_factor

            return base_score

        return sorted(movie_data, key=bayesian_score)

    def _sort_weight_with_a_res(self, movie_data: list[dict], rng) -> list[dict]:
        weighted_sort_list = []
        for item in movie_data:
            m_id = item['id']
            weight = max(item['weight'], 0.0001)
            u = rng.random()
            key = u ** (1.0 / weight)  # Calculate A-Res key
            weighted_sort_list.append((key, m_id))

        weighted_sort_list.sort(key=lambda x: x[0], reverse=True)
        return weighted_sort_list

    @alru_cache(maxsize=128)
    async def get_movie_ids(self, list_id: uuid.UUID, offset: int, limit: int) -> tuple[list[uuid.UUID], int]:
        pg_start = offset + 1
        pg_end = offset + limit

        # FIXME: This is a leaky abstraction. DB access belongs in the repositories
        stmt = select(
            PreShuffledMovieList.movie_ids[pg_start:pg_end], func.array_length(PreShuffledMovieList.movie_ids, 1)
        ).where(PreShuffledMovieList.id == list_id)

        result = await self.repo.db.execute(stmt)
        row = result.first()

        if not row:
            return ([], 0)

        movie_ids_slice, total_count = row

        if not movie_ids_slice:
            movie_ids_slice = []

        return (movie_ids_slice, total_count)


class UserService(BaseService[User, UserRepository]):
    """Service for managing users."""

    def __init__(self, user_repo: UserRepository):
        """Initialize the user service."""
        self.repo = user_repo

    async def get_user_by_auth0_sub(self, token_user: str) -> User | None:
        """Retrieve a user by their Auth0 sub."""
        return await self.repo.find_one(RepoQueryOptions(filters={'auth0_sub': token_user}))

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their UUID."""
        return await self.repo.find_one(RepoQueryOptions(ids=[user_id]))

    async def create_user_from_auth0(self, token_user: Auth0UserSchema) -> User:
        """Create a new user from an Auth0 token."""
        new_user = User(
            auth0_sub=token_user.sub,
            email=token_user.email,
            desc=token_user.name,
            picture=token_user.picture,
        )

        await self.repo.create(new_user)

        return new_user

    async def update_user_from_auth0(self, db_user: User, token_user: Auth0UserSchema) -> User:
        """Update local user details if they differ from Auth0 token."""
        updates = {}
        if token_user.email is not None and db_user.email != token_user.email:
            updates['email'] = token_user.email
        if token_user.name is not None and db_user.desc != token_user.name:
            updates['desc'] = token_user.name
        if token_user.picture is not None and db_user.picture != token_user.picture:
            updates['picture'] = token_user.picture

        if updates:
            await self.repo.update(db_user.id, updates)
            for key, value in updates.items():
                setattr(db_user, key, value)

        return db_user

    async def search_users(self, query: str) -> Sequence[User]:
        """Search users by email or description."""
        options = RepoQueryOptions(
            search_text=query,
            search_columns=['email', 'desc'],
        )
        return await self.repo.find_many(options)
