from typing import Annotated

from fastapi import Form
from pydantic import EmailStr


class OAuth2EmailRequestForm:
    """
    OAuth2-compatible login form using email instead of username.
    """

    def __init__(
        self,
        email: Annotated[EmailStr, Form()],
        password: Annotated[str, Form()],
    ):
        self.email = email
        self.password = password
