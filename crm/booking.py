from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select


# -------------------------------------------------------------
# DATABASE MODEL
# -------------------------------------------------------------
class Booking(SQLModel, table=True):
    """Represents a customer booking record."""
    id: int | None = Field(default=None, primary_key=True)
    customer_name: str
    phone_number: str
    booking_time: datetime       # When the booking starts
    duration_minutes: int = 60   # Length of booking in minutes


# Response model with human-readable time
class BookingPublic(SQLModel):
    id: int
    customer_name: str
    phone_number: str
    booking_time: str            # e.g. "2025-11-23 10:40"
    duration_minutes: int

    @classmethod
    def from_orm(cls, booking: Booking):
        """Convert DB model → readable format."""
        return cls(
            id=booking.id,
            customer_name=booking.customer_name,
            phone_number=booking.phone_number,
            booking_time=booking.booking_time.strftime("%Y-%m-%d %H:%M"),
            duration_minutes=booking.duration_minutes
        )


class BookingCreate(SQLModel):
    """Input schema when creating a booking."""
    customer_name: str
    phone_number: str
    booking_time: datetime
    duration_minutes: int = 60


class BookingUpdate(SQLModel):
    """Input schema when updating a booking."""
    customer_name: str | None = None
    phone_number: str | None = None
    booking_time: datetime | None = None
    duration_minutes: int | None = None


# -------------------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------------------
sqlite_file_name = "bookings.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    create_db_and_tables()
    yield


# -------------------------------------------------------------
# FASTAPI SETUP
# -------------------------------------------------------------
SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI(title="Simple Booking API", lifespan=lifespan)


# -------------------------------------------------------------
# CRUD ENDPOINTS
# -------------------------------------------------------------
@app.post("/bookings/", response_model=BookingPublic)
def create_booking(booking: BookingCreate, session: SessionDep):
    """Create a new booking (no overlapping time slots)."""

    # Fix timezone-aware datetime (e.g. 'Z' at end)
    if booking.booking_time.tzinfo is not None:
        booking.booking_time = booking.booking_time.replace(tzinfo=None)

    new_start = booking.booking_time
    new_end = new_start + timedelta(minutes=booking.duration_minutes)

    # Check for time conflicts
    for b in session.exec(select(Booking)).all():
        existing_start = b.booking_time
        existing_end = existing_start + timedelta(minutes=b.duration_minutes)
        if new_start < existing_end and new_end > existing_start:
            raise HTTPException(status_code=400, detail="Time slot already booked.")

    db_booking = Booking.model_validate(booking)
    session.add(db_booking)
    session.commit()
    session.refresh(db_booking)
    return BookingPublic.from_orm(db_booking)


@app.get("/bookings/", response_model=list[BookingPublic])
def list_bookings(session: SessionDep):
    """List all bookings."""
    bookings = session.exec(select(Booking)).all()
    return [BookingPublic.from_orm(b) for b in bookings]


@app.get("/bookings/{booking_id}", response_model=BookingPublic)
def get_booking(booking_id: int, session: SessionDep):
    """Get booking by ID."""
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingPublic.from_orm(booking)


@app.patch("/bookings/{booking_id}", response_model=BookingPublic)
def update_booking(booking_id: int, update: BookingUpdate, session: SessionDep):
    """Update a booking (also checks for overlapping times)."""
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    data = update.model_dump(exclude_unset=True)

    # Handle timezone in updates
    if "booking_time" in data and data["booking_time"].tzinfo is not None:
        data["booking_time"] = data["booking_time"].replace(tzinfo=None)

    new_start = data.get("booking_time", booking.booking_time)
    new_duration = data.get("duration_minutes", booking.duration_minutes)
    new_end = new_start + timedelta(minutes=new_duration)

    # Validate time conflicts
    for b in session.exec(select(Booking)).all():
        if b.id == booking_id:
            continue
        existing_start = b.booking_time
        existing_end = existing_start + timedelta(minutes=b.duration_minutes)
        if new_start < existing_end and new_end > existing_start:
            raise HTTPException(status_code=400, detail="Time slot already booked.")

    booking.sqlmodel_update(data)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return BookingPublic.from_orm(booking)


@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int, session: SessionDep):
    """Delete a booking by ID."""
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    session.delete(booking)
    session.commit()
    return {"ok": True}
