"""
User role service.
"""

from app.models.users.user_roles import UserRole
from app.repositories.users.user_role_repository import UserRoleRepository
from app.schemas.users.user_roles import UserRoleCreate, UserRoleUpdate
from app.services.base_service import BaseService


class UserRoleService(BaseService[UserRole, UserRoleCreate, UserRoleUpdate]):
    """
    Service for UserRole business logic.
    """

    def __init__(self, repository: UserRoleRepository):
        super().__init__(repository, "User role")
