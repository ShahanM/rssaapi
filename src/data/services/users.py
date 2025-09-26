from data.models.study_components import User
from data.repositories.user_repo import UserRepository
from data.schemas import Auth0UserSchema


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.repo = user_repo

    async def get_user_by_auth0_sub(self, token_user: str) -> User:
        return await self.repo.get_by_field('auth0_sub', token_user)

    async def create_user_from_auth0(self, token_user: Auth0UserSchema) -> User:
        new_user = User(auth0_sub=Auth0UserSchema.sub)

        await self.repo.create(new_user)

        return new_user
