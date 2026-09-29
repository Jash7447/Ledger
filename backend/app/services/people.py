from collections import defaultdict
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.models.enums import IOUAdjustmentDirection, IOUEventType
from app.models.iou_event import IOUEvent
from app.models.person import Person
from app.schemas.people import (
    IOUEventCreate,
    IOUEventResponse,
    IOUEventUpdate,
    IOUTotals,
    PersonCreate,
    PersonDetail,
    PersonSummary,
    PersonUpdate,
)

ZERO = Decimal("0.00")


def list_people(db: Session, user_id: UUID) -> list[PersonSummary]:
    people = list(
        db.scalars(
            select(Person)
            .where(Person.user_id == user_id)
            .order_by(Person.name.asc())
        ).all()
    )
    events_by_person = _events_by_person(db, user_id)
    return [_person_summary(person, events_by_person.get(person.id, [])) for person in people]


def get_person(db: Session, user_id: UUID, person_id: UUID) -> PersonDetail:
    person = _get_person(db, user_id, person_id)
    events = list(
        db.scalars(
            select(IOUEvent)
            .where(IOUEvent.user_id == user_id, IOUEvent.person_id == person_id)
            .order_by(IOUEvent.date.asc(), IOUEvent.created_at.asc())
        ).all()
    )
    summary = _person_summary(person, events)
    running = ZERO
    responses: list[IOUEventResponse] = []
    for event in events:
        effect = event_effect(event)
        running += effect
        responses.append(_event_response(event, effect, running))
    return PersonDetail(
        **summary.model_dump(),
        notes=person.notes,
        created_at=person.created_at,
        updated_at=person.updated_at,
        events=list(reversed(responses)),
    )


def create_person(db: Session, user_id: UUID, data: PersonCreate) -> PersonDetail:
    person = Person(user_id=user_id, name=data.name.strip(), notes=data.notes)
    db.add(person)
    _commit_person(db)
    db.refresh(person)
    return get_person(db, user_id, person.id)


def update_person(
    db: Session, user_id: UUID, person_id: UUID, data: PersonUpdate
) -> PersonDetail:
    person = _get_person(db, user_id, person_id)
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is not None:
        changes["name"] = changes["name"].strip()
    for field, value in changes.items():
        setattr(person, field, value)
    _commit_person(db)
    db.refresh(person)
    return get_person(db, user_id, person.id)


def delete_person(db: Session, user_id: UUID, person_id: UUID) -> None:
    person = _get_person(db, user_id, person_id)
    db.delete(person)
    db.commit()


def create_event(
    db: Session, user_id: UUID, person_id: UUID, data: IOUEventCreate
) -> IOUEventResponse:
    _get_person(db, user_id, person_id)
    event = IOUEvent(user_id=user_id, person_id=person_id, **data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return _response_in_person_history(db, user_id, person_id, event.id)


def update_event(
    db: Session,
    user_id: UUID,
    person_id: UUID,
    event_id: UUID,
    data: IOUEventUpdate,
) -> IOUEventResponse:
    event = _get_event(db, user_id, person_id, event_id)
    current = IOUEventCreate(
        event_type=event.event_type,
        amount_cad=event.amount_cad,
        date=event.date,
        adjustment_direction=event.adjustment_direction,
        notes=event.notes,
    ).model_dump()
    current.update(data.model_dump(exclude_unset=True))
    merged = IOUEventCreate.model_validate(current)
    for field, value in merged.model_dump().items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return _response_in_person_history(db, user_id, person_id, event.id)


def delete_event(
    db: Session, user_id: UUID, person_id: UUID, event_id: UUID
) -> None:
    event = _get_event(db, user_id, person_id, event_id)
    db.delete(event)
    db.commit()


def get_iou_totals(db: Session, user_id: UUID) -> IOUTotals:
    totals: dict[UUID, Decimal] = defaultdict(lambda: ZERO)
    for event in db.scalars(
        select(IOUEvent).where(IOUEvent.user_id == user_id)
    ).all():
        totals[event.person_id] += event_effect(event)
    return IOUTotals(
        owed_to_user_cad=sum((value for value in totals.values() if value > 0), ZERO),
        user_owes_cad=sum((-value for value in totals.values() if value < 0), ZERO),
    )


def event_effect(event: IOUEvent) -> Decimal:
    if event.event_type in {IOUEventType.LENT, IOUEventType.REPAYMENT_MADE}:
        return event.amount_cad
    if event.event_type in {
        IOUEventType.BORROWED,
        IOUEventType.REPAYMENT_RECEIVED,
    }:
        return -event.amount_cad
    if event.adjustment_direction == IOUAdjustmentDirection.OWES_USER:
        return event.amount_cad
    return -event.amount_cad


def _get_person(db: Session, user_id: UUID, person_id: UUID) -> Person:
    person = db.scalar(
        select(Person).where(Person.id == person_id, Person.user_id == user_id)
    )
    if person is None:
        raise ResourceNotFoundError("Person")
    return person


def _get_event(
    db: Session, user_id: UUID, person_id: UUID, event_id: UUID
) -> IOUEvent:
    _get_person(db, user_id, person_id)
    event = db.scalar(
        select(IOUEvent).where(
            IOUEvent.id == event_id,
            IOUEvent.person_id == person_id,
            IOUEvent.user_id == user_id,
        )
    )
    if event is None:
        raise ResourceNotFoundError("IOU event")
    return event


def _events_by_person(db: Session, user_id: UUID) -> dict[UUID, list[IOUEvent]]:
    result: dict[UUID, list[IOUEvent]] = defaultdict(list)
    for event in db.scalars(
        select(IOUEvent)
        .where(IOUEvent.user_id == user_id)
        .order_by(IOUEvent.date.asc(), IOUEvent.created_at.asc())
    ).all():
        result[event.person_id].append(event)
    return result


def _person_summary(person: Person, events: list[IOUEvent]) -> PersonSummary:
    balance = sum((event_effect(event) for event in events), ZERO)
    direction: Literal["owed_to_user", "user_owes", "settled"]
    if balance > 0:
        direction = "owed_to_user"
    elif balance < 0:
        direction = "user_owes"
    else:
        direction = "settled"
    return PersonSummary(
        id=person.id,
        name=person.name,
        direction=direction,
        outstanding_amount_cad=abs(balance),
        last_activity=max((event.date for event in events), default=None),
        event_count=len(events),
    )


def _event_response(
    event: IOUEvent, effect: Decimal, running_balance: Decimal
) -> IOUEventResponse:
    return IOUEventResponse(
        id=event.id,
        person_id=event.person_id,
        event_type=event.event_type,
        adjustment_direction=event.adjustment_direction,
        amount_cad=event.amount_cad,
        date=event.date,
        notes=event.notes,
        effect_cad=effect,
        running_balance_cad=running_balance,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _response_in_person_history(
    db: Session, user_id: UUID, person_id: UUID, event_id: UUID
) -> IOUEventResponse:
    detail = get_person(db, user_id, person_id)
    return next(event for event in detail.events if event.id == event_id)


def _commit_person(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ResourceConflictError("A person with this name already exists") from error
