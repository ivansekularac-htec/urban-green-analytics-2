"""
Role service.
"""

from app.models.users.role import Role
from app.repositories.users.role import RoleRepository
from app.schemas.users.role import RoleCreate, RoleUpdate
from app.services.base_service import BaseService


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    """
    Service for Role business logic.
    """

    def __init__(self, repository: RoleRepository):
        super().__init__(repository, "Role")
