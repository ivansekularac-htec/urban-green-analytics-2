# from pydantic import BaseModel, EmailStr


# class RegisterRequest(BaseModel):
#     email: EmailStr
#     password: str
#     full_name: str


# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str


# class TokenResponse(BaseModel):
#     access_token: str
#     token_type: str = "bearer"


from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=255,
    )
    full_name: str = Field(
        min_length=1,
        max_length=255,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=255,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
