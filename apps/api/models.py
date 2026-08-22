"""SQLAlchemy models for the api service.

Schema matches the ER diagram in `_docs/outdated/architecture.md` §4.3:

    MEMBER ||--o| COVERAGE : has
    PLAN   ||--o{ COVERAGE : covers

Each member has at most one coverage segment (plan.md's "single coverage
segment per member"), so `Coverage.member_id` is both the foreign key to
`Member` and the coverage table's primary key.
"""

import datetime

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "members"

    member_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    coverage: Mapped["Coverage | None"] = relationship(
        back_populates="member", uselist=False
    )


class Plan(Base):
    __tablename__ = "plans"

    plan_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    coverages: Mapped[list["Coverage"]] = relationship(back_populates="plan")


class Coverage(Base):
    __tablename__ = "coverages"

    member_id: Mapped[str] = mapped_column(
        ForeignKey("members.member_id"), primary_key=True
    )
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.plan_id"), nullable=False)
    effective_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[datetime.date | None] = mapped_column(
        Date, nullable=True
    )

    member: Mapped["Member"] = relationship(back_populates="coverage")
    plan: Mapped["Plan"] = relationship(back_populates="coverages")
