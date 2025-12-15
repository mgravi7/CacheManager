from typing import Optional, List
from uuid import UUID
from .models import User, UserInternal
from cache_manager import CacheManager

# Hardcoded sample users for POC
SAMPLE_USERS = [
    UserInternal(
        id=1,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440001"),
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com"
    ),
    UserInternal(
        id=2,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440002"),
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com"
    ),
    UserInternal(
        id=3,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440003"),
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com"
    ),
    UserInternal(
        id=4,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440004"),
        first_name="Alice",
        last_name="Williams",
        email="alice.williams@example.com"
    ),
    UserInternal(
        id=5,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440005"),
        first_name="Charlie",
        last_name="Brown",
        email="charlie.brown@example.com"
    ),
    UserInternal(
        id=6,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440006"),
        first_name="Diana",
        last_name="Davis",
        email="diana.davis@example.com"
    ),
    UserInternal(
        id=7,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440007"),
        first_name="Edward",
        last_name="Miller",
        email="edward.miller@example.com"
    ),
    UserInternal(
        id=8,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440008"),
        first_name="Fiona",
        last_name="Wilson",
        email="fiona.wilson@example.com"
    ),
    UserInternal(
        id=9,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440009"),
        first_name="George",
        last_name="Moore",
        email="george.moore@example.com"
    ),
    UserInternal(
        id=10,
        uuid=UUID("550e8400-e29b-41d4-a716-446655440010"),
        first_name="Hannah",
        last_name="Taylor",
        email="hannah.taylor@example.com"
    ),
]

# Index for quick lookups
USERS_BY_ID = {user.id: user for user in SAMPLE_USERS}
USERS_BY_UUID = {user.uuid: user for user in SAMPLE_USERS}


class UserDAL:
    """Data Access Layer for User operations with cache integration."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    async def get_all_users(self) -> List[User]:
        """Retrieve all users."""
        return [
            User(
                uuid=user.uuid,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email
            )
            for user in SAMPLE_USERS
        ]

    async def get_user_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        """
        Retrieve user by UUID with cache integration.
        Cache flow: UUID -> ID (from cache) -> User data
        """
        # Try to get ID from UUID cache
        user_id = await self.cache_manager.uuid_to_id_cache.get(user_uuid)
        
        if user_id is not None:
            # Cache hit - get user by ID
            user_internal = USERS_BY_ID.get(user_id)
        else:
            # Cache miss - lookup by UUID in data source
            user_internal = USERS_BY_UUID.get(user_uuid)
            
            if user_internal:
                # Populate both caches
                await self.cache_manager.uuid_to_id_cache.set(user_uuid, user_internal.id)
                await self.cache_manager.id_to_uuid_cache.set(user_internal.id, user_uuid)

        if user_internal is None:
            return None

        return User(
            uuid=user_internal.uuid,
            first_name=user_internal.first_name,
            last_name=user_internal.last_name,
            email=user_internal.email
        )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID with cache integration.
        Cache flow: ID -> UUID (from cache) -> User data
        Note: This method is internal and not exposed via API.
        """
        # Try to get UUID from ID cache
        user_uuid = await self.cache_manager.id_to_uuid_cache.get(user_id)
        
        if user_uuid is not None:
            # Cache hit - get user by UUID
            user_internal = USERS_BY_UUID.get(user_uuid)
        else:
            # Cache miss - lookup by ID in data source
            user_internal = USERS_BY_ID.get(user_id)
            
            if user_internal:
                # Populate both caches
                await self.cache_manager.id_to_uuid_cache.set(user_id, user_internal.uuid)
                await self.cache_manager.uuid_to_id_cache.set(user_internal.uuid, user_id)

        if user_internal is None:
            return None

        return User(
            uuid=user_internal.uuid,
            first_name=user_internal.first_name,
            last_name=user_internal.last_name,
            email=user_internal.email
        )
