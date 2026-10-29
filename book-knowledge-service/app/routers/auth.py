"""app/routers/auth.py – login / logout / whoami and admin student management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from .. import auth
from ..auth import User, require_admin, require_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
    role: str = Field(..., description="'admin' or 'student'")


class StudentCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class UserInfo(BaseModel):
    username: str
    role: str


class StudentList(BaseModel):
    students: list[str]
    total: int


@router.post("/login", response_model=UserInfo)
async def login(req: LoginRequest, request: Request, response: Response):
    username = req.username.strip()
    if not auth.authenticate(username, req.password, req.role):
        raise HTTPException(status_code=401, detail="Invalid username, password or user type.")

    # Drop any session this browser already holds before issuing a new one.
    auth.destroy_session(request.cookies.get(auth.SESSION_COOKIE))
    user = User(username=username, role=req.role)
    response.set_cookie(
        auth.SESSION_COOKIE,
        auth.create_session(user),
        max_age=auth.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return UserInfo(username=user.username, role=user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    auth.destroy_session(request.cookies.get(auth.SESSION_COOKIE))
    response.delete_cookie(auth.SESSION_COOKIE)


@router.get("/me", response_model=UserInfo)
async def me(user: User = Depends(require_user)):
    return UserInfo(username=user.username, role=user.role)


@router.get("/students", response_model=StudentList)
async def list_students(_: User = Depends(require_admin)):
    names = auth.list_students()
    return StudentList(students=names, total=len(names))


@router.post("/students", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def add_student(req: StudentCreate, _: User = Depends(require_admin)):
    username = req.username.strip()
    try:
        auth.add_student(username, req.password)
    except auth.DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UserInfo(username=username, role=auth.ROLE_STUDENT)
