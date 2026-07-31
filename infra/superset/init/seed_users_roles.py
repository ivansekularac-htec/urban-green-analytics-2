"""Seed Superset business roles and users."""

from __future__ import annotations

import os
from dataclasses import dataclass

from superset.app import create_app


@dataclass(frozen=True)
class UserSeed:
    username: str
    first_name: str
    last_name: str
    email: str
    password_env: str
    business_role: str


USER_SEEDS = (
    UserSeed(
        username=os.getenv("FARM_MANAGER_USERNAME", "manager"),
        first_name=os.getenv("FARM_MANAGER_FIRSTNAME", "Farm"),
        last_name=os.getenv("FARM_MANAGER_LASTNAME", "Manager"),
        email=os.getenv(
            "FARM_MANAGER_EMAIL",
            "manager@urbangreen.com",
        ),
        password_env="FARM_MANAGER_PASSWORD",
        business_role="Manager",
    ),
    UserSeed(
        username=os.getenv(
            "OPERATIONS_TEAM_USERNAME",
            "operations",
        ),
        first_name=os.getenv(
            "OPERATIONS_TEAM_FIRSTNAME",
            "Operations",
        ),
        last_name=os.getenv(
            "OPERATIONS_TEAM_LASTNAME",
            "Team",
        ),
        email=os.getenv(
            "OPERATIONS_TEAM_EMAIL",
            "operations@urbangreen.com",
        ),
        password_env="OPERATIONS_TEAM_PASSWORD",
        business_role="Operations Team",
    ),
)


def seed_users_and_roles() -> None:
    """Create or update Superset business users and roles."""

    app = create_app()

    with app.app_context():
        security_manager = app.appbuilder.sm

        gamma_role = security_manager.find_role("Gamma")

        if gamma_role is None:
            raise RuntimeError("Gamma role does not exist. Run 'superset init' first.")

        business_roles = {
            role_name: security_manager.add_role(role_name)
            for role_name in ("Manager", "Operations Team")
        }

        if any(role is None for role in business_roles.values()):
            raise RuntimeError("Could not create Superset business roles.")

        for user_seed in USER_SEEDS:
            assigned_roles = [
                gamma_role,
                business_roles[user_seed.business_role],
            ]

            existing_user = security_manager.find_user(
                username=user_seed.username,
            )

            if existing_user is None:
                created_user = security_manager.add_user(
                    username=user_seed.username,
                    first_name=user_seed.first_name,
                    last_name=user_seed.last_name,
                    email=user_seed.email,
                    role=assigned_roles,
                    password=os.getenv(user_seed.password_env),
                )

                if not created_user:
                    raise RuntimeError(
                        f"Could not create Superset user {user_seed.username!r}."
                    )

                print(f"Created Superset user: {user_seed.username}")
                continue

            existing_user.first_name = user_seed.first_name
            existing_user.last_name = user_seed.last_name
            existing_user.email = user_seed.email
            existing_user.active = True
            existing_user.roles = assigned_roles

            update_result = security_manager.update_user(
                existing_user,
            )

            if update_result is False:
                raise RuntimeError(
                    f"Could not update Superset user {user_seed.username!r}."
                )

            print(f"Updated Superset user: {user_seed.username}")

        print("Superset users and roles seeded successfully.")


if __name__ == "__main__":
    seed_users_and_roles()
