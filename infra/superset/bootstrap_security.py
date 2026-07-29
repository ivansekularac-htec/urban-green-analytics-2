from superset.app import create_app
from superset.extensions import db

app = create_app()


DEMO_USERS = [
    {
        "username": "fm1",
        "first_name": "Farm",
        "last_name": "Manager",
        "email": "fm1@urbangreen.com",
        "password": "fm123",
        "roles": ["Gamma", "FarmManager"],
    },
    {
        "username": "ot1",
        "first_name": "Operations",
        "last_name": "Team",
        "email": "ot1@urbangreen.com",
        "password": "ot123",
        "roles": ["Gamma", "OperationsTeam"],
    },
]


def get_or_create_role(security_manager, name: str):
    role = security_manager.find_role(name)

    if role is None:
        role = security_manager.add_role(name)
        db.session.commit()
        print(f"Created role: {name}")
    else:
        print(f"Role already exists: {name}")

    return role


def get_or_create_user(security_manager, user_data: dict):
    user = security_manager.find_user(username=user_data["username"])

    if user is not None:
        print(f"User '{user_data['username']}' already exists.")
        return user

    default_role = security_manager.find_role("Gamma")

    if default_role is None:
        raise Exception("Default role 'Gamma' does not exist.")

    user = security_manager.add_user(
        username=user_data["username"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        email=user_data["email"],
        role=default_role,
        password=user_data["password"],
    )

    if user is None:
        raise Exception(f"Failed creating user '{user_data['username']}'.")

    db.session.commit()

    print(f"Created user '{user_data['username']}'.")

    return user


def assign_role(security_manager, username: str, role_name: str):
    user = security_manager.find_user(username=username)

    if user is None:
        print(f"User '{username}' not found.")
        return

    role = security_manager.find_role(role_name)

    if role is None:
        print(f"Role '{role_name}' not found.")
        return

    if role in user.roles:
        print(f"User '{username}' already has role '{role_name}'.")
        return

    user.roles.append(role)

    db.session.commit()

    print(f"Assigned role '{role_name}' to '{username}'.")


def main():
    with app.app_context():
        security_manager = app.appbuilder.sm

        print("Creating demo roles and users...")

        get_or_create_role(
            security_manager,
            "FarmManager",
        )

        get_or_create_role(
            security_manager,
            "OperationsTeam",
        )

        # Create users
        for user in DEMO_USERS:
            get_or_create_user(
                security_manager,
                user,
            )

        # Assign custom roles
        for user in DEMO_USERS:
            for role in user["roles"]:
                assign_role(
                    security_manager,
                    user["username"],
                    role,
                )

        print("Demo users and roles initialized.")


if __name__ == "__main__":
    main()
