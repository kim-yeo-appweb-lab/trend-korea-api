from sqlalchemy import Enum as _SAEnum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def ValueEnum(enum_cls):
    """DB에 Enum의 .value(소문자)를 저장하도록 매핑한다."""
    return _SAEnum(enum_cls, values_callable=lambda e: [x.value for x in e])
