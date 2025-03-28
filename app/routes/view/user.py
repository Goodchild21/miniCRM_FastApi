import json
import uuid
from datetime import datetime

import nh3
from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi_csrf_protect import CsrfProtect

from app.database.db import CurrentAsyncSession
from app.database.security import current_active_user
from app.models.users import Role as RoleModelDB
from app.models.users import User as UserModelDB
from app.models.users import UserProfile as UserProfileModelDB
from app.routes.view.errors import handle_error
from app.routes.view.view_crud import SQLAlchemyCRUD
from app.schema.users import ProfileUpdate

from app.templates import templates

# APIRouter
user_view_route = APIRouter()


user_crud = SQLAlchemyCRUD[UserModelDB](
    UserModelDB, related_models={RoleModelDB: "role", UserProfileModelDB: "profile"}
)
user_profile_crud = SQLAlchemyCRUD[UserProfileModelDB](UserProfileModelDB)

role_crud = SQLAlchemyCRUD[RoleModelDB](RoleModelDB)


@user_view_route.get("/user", response_class=HTMLResponse)
async def get_users(
    request: Request,
    db: CurrentAsyncSession,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Вы не авторизованы для этой страницы"
            )

        # Access the cookies using the Request object
        token = request.cookies.get("fastapiusersauth")
        users = await user_crud.read_all(db, skip, limit, join_relationships=True)

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        response = templates.TemplateResponse(
            "pages/user.html",
            {
                "request": request,
                "users": users,
                "token": token,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
        )

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        token = request.cookies.get("fastapiusersauth")
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "pages/user.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "token": token,
                "user_type": current_user.is_superuser,
            },
            e,
        )


@user_view_route.get("/get_create_users", response_class=HTMLResponse)
async def get_create_users(
    request: Request,
    current_user: UserModelDB = Depends(current_active_user),
):

    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления данных!")
        # Redirecting to the add role page upon successful role creation
        return templates.TemplateResponse(
            "partials/user/add_user.html",
            {"request": request},
        )
    except Exception as e:
        return handle_error("partials/user/add_user.html", {"request": request}, e)


# Эндпоинт для получения записи на основе идентификатора
@user_view_route.get("/get_user/{user_id}", response_class=HTMLResponse)
async def get_user_by_id(
    request: Request,
    user_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    try:
        roles = await role_crud.read_all(db, skip, limit)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Вы не авторизованы для этой страницы"
            )
        user = await user_crud.read_by_primary_key(db, user_id, join_relationships=True)

        csrf_token = request.headers.get("X-CSRF-Token")

        return templates.TemplateResponse(
            "partials/user/edit_user.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "user_type": current_user.is_superuser,
                "csrf_token": csrf_token,
            },
        )
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/user/edit_user.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "user_type": current_user.is_superuser,
                "csrf_token": csrf_token,
            },
            e,
        )


# Эндпоинт для обновления записи на основе идентификатора
@user_view_route.put("/post_update_user/{user_id}", response_class=HTMLResponse)
async def post_update_user(
    request: Request,
    # response: Response,
    user_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):

    try:
        await csrf_protect.validate_csrf(request)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления данных!")

        form = await request.form()
        # Очистка полей формы перед проверкой по модели Pydantic
        profile_data = ProfileUpdate(
            first_name=nh3.clean(str(form.get("first_name"))),
            last_name=nh3.clean(str(form.get("last_name"))),
            gender=nh3.clean(str(form.get("gender"))),
            date_of_birth=(
                datetime.strptime(nh3.clean(str(form.get("dob"))), "%Y-%m-%d")
                if form.get("dob")
                else None
            ),
            address=nh3.clean(str(form.get("address"))),
            city=nh3.clean(str(form.get("city"))),
            country=nh3.clean(str(form.get("country"))),
            phone=nh3.clean(str(form.get("phone"))),
            company=nh3.clean(str(form.get("company"))),
        )

        role_id = (nh3.clean(str(form.get("role_id"))),)
        role_id = uuid.UUID(role_id[0]) if role_id[0] else None

        if role_id is None:
            raise HTTPException(
                status_code=400, detail="Необходима роль для создания профиля пользователя"
            )

        # Пользователь обновляется
        user_to_update = await user_crud.read_by_primary_key(db, user_id)

        if user_to_update.profile_id is None:
            # Создать профиль
            new_profile = await user_profile_crud.create(dict(profile_data), db)

            # Обновить профиль по id
            await user_crud.update(db, user_id, {"profile_id": new_profile.id})

            # Обновить роль
            if role_id:
                await user_crud.update(db, user_id, {"role_id": role_id})

            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
            headers = {
                "HX-Location": "/user",
                "HX-Trigger": json.dumps(
                    {
                        "showAlert": {
                            "type": "updated",
                            "message": f"Роль для {profile_data.first_name , profile_data.last_name} обновлена!",
                            "source": "user-page",
                        },
                    }
                ),
                "csrf_token": csrf_token,
            }
            response = HTMLResponse(content="", headers=headers)

            csrf_protect.unset_csrf_cookie(response)

            csrf_protect.set_csrf_cookie(signed_token, response)

            return response
        else:
            # Обновить существующий профиль
            await user_profile_crud.update(
                db, user_to_update.profile_id, dict(profile_data)
            )

            # Редактировать существующий профиль
            if role_id:
                await user_crud.update(db, user_id, {"role_id": role_id})

            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

            headers = {
                "HX-Location": "/user",
                "HX-Trigger": json.dumps(
                    {
                        "showAlert": {
                            "type": "updated",
                            "message": f"Профиль {profile_data.first_name , profile_data.last_name} обновлен!",
                            "source": "user-page",
                        },
                    }
                ),
                "csrf_token": csrf_token,
            }
            response = HTMLResponse(content="", headers=headers)

            csrf_protect.unset_csrf_cookie(response)

            csrf_protect.set_csrf_cookie(signed_token, response)

            return response
    except Exception as e:
        user = await user_crud.read_by_primary_key(db, user_id, join_relationships=True)
        roles = await role_crud.read_all(db)
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/user/edit_user.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "csrf_token": csrf_token,
            },
            e,
        )
