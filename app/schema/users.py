import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi_users import schemas
from pydantic import UUID4, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from .pydantic_base import pydantic_partial

PasswordStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=8)]


class UserRead(schemas.BaseUser[uuid.UUID]):
    email: EmailStr

    class Config:
        # Exclude the unwanted fields from the schema
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
            }
        }


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    # Ограничение к новому пользователю, созданному с минимальной длиной пароля
    password: PasswordStr

    class Config:
        # Исключить нежелательные поля из shema
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "strings"}
        }


class UserUpdate(schemas.BaseUserUpdate):
    # Применение ограничений к новому пользователю, созданному с минимальной длиной пароля
    password: PasswordStr

    class Config:
        # Исключить нежелательные поля из shema
        json_schema_extra = {"example": {"password": "strings"}}


class RoleBase(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    role_name: str = Field(
        ...,
        title="Role Name",
        description="Role Name",
        min_length=3,
        max_length=50,
    )
    role_desc: Annotated[
        Optional[str],
        Field(
            min_length=5,
            max_length=200,
            examples=["Role description is provided here"],
            title="Role Description",
            default=None,
        ),
    ]
    role_id: Optional[UUID4] = Field(
        default_factory=uuid.uuid4,
        title="Role ID",
        description="Role ID",
    )

    # @validator("role_desc")
    # def validate_role_desc(cls, v):
    #     if v == "":
    #         return None
    #     elif len(v) < 5:
    #         raise ValueError("String should have at least 5 characters")
    #     return v


# Модель Pydantic для чтения роли на основе идентификатора и без учета role_name и role_desc
RoleRead = pydantic_partial(exclude_fields=["role_name", "role_desc"])(RoleBase)
# Модель Pydantic для создания роли с role_name и role_desc и без id
RoleCreate = pydantic_partial(exclude_fields=["role_id"])(RoleBase)


class RoleUpdate(RoleBase):
    pass


class ProfileBase(BaseModel):

    model_config = ConfigDict(hide_input_in_errors=True)

    first_name: str = Field(
        ...,
        title="First Name",
        description="First Name",
        min_length=3,
        max_length=120,
    )
    last_name: str = Field(
        ...,
        title="Last Name",
        description="Last Name",
        min_length=3,
        max_length=120,
    )
    gender: Annotated[
        Optional[str],
        Field(
            min_length=3,
            max_length=10,
            title="Gender",
        ),
    ]
    date_of_birth: Annotated[
        Optional[datetime],
        Field(
            title="Date of Birth",
        ),
    ]
    city: Annotated[
        Optional[str],
        Field(
            min_length=0,
            max_length=50,
            title="City",
        ),
    ]
    country: Annotated[
        Optional[str],
        Field(
            min_length=0,
            max_length=50,
            title="Country",
        ),
    ]
    address: Annotated[
        Optional[str],
        Field(
            min_length=0,
            max_length=255,
            title="Address",
        ),
    ]
    phone: Annotated[
        Optional[str],
        Field(
            min_length=0,
            max_length=15,
            title="Phone Number",
        ),
    ]
    company: Annotated[
        Optional[str],
        Field(
            min_length=0,
            max_length=100,
            title="Company",
        ),
    ]
    user_id: Optional[UUID4] = Field(
        default_factory=uuid.uuid4,
        title="User ID",
        description="User ID",
    )


# Модель Pydantic для обновления роли
ProfileUpdate = pydantic_partial(exclude_fields=["user_id"])(ProfileBase)
