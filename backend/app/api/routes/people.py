from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.people import (
    IOUEventCreate,
    IOUEventResponse,
    IOUEventUpdate,
    PersonCreate,
    PersonDetail,
    PersonSummary,
    PersonUpdate,
)
from app.services.people import (
    create_event,
    create_person,
    delete_event,
    delete_person,
    get_person,
    list_people,
    update_event,
    update_person,
)

router = APIRouter()


@router.get("", response_model=list[PersonSummary])
def list_all(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[PersonSummary]:
    return list_people(db, current_user.id)


@router.post("", response_model=PersonDetail, status_code=status.HTTP_201_CREATED)
def create(
    data: PersonCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PersonDetail:
    return create_person(db, current_user.id, data)


@router.get("/{person_id}", response_model=PersonDetail)
def get(
    person_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PersonDetail:
    return get_person(db, current_user.id, person_id)


@router.patch("/{person_id}", response_model=PersonDetail)
def update(
    person_id: UUID,
    data: PersonUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PersonDetail:
    return update_person(db, current_user.id, person_id, data)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    person_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_person(db, current_user.id, person_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{person_id}/events",
    response_model=IOUEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_event(
    person_id: UUID,
    data: IOUEventCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> IOUEventResponse:
    return create_event(db, current_user.id, person_id, data)


@router.patch("/{person_id}/events/{event_id}", response_model=IOUEventResponse)
def edit_event(
    person_id: UUID,
    event_id: UUID,
    data: IOUEventUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> IOUEventResponse:
    return update_event(db, current_user.id, person_id, event_id, data)


@router.delete(
    "/{person_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_event(
    person_id: UUID,
    event_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_event(db, current_user.id, person_id, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
