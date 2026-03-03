"""한국소비자원 생필품 가격 정보 모델.

테이블 구조:
  product_info   — 상품 마스터 정보 (goodId, 상품명, 단위, 용량 등)
  product_prices — 가격 정보 (판매가격, 판매업소, 세일 여부 등)
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class ProductInfo(Base):
    """상품 마스터 정보. 한국소비자원 API goodId 기준 유니크."""

    __tablename__ = "product_info"
    __table_args__ = (Index("ix_pi_fetched_at", "fetched_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    good_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    good_name: Mapped[str] = mapped_column(String(70), nullable=False)
    good_unit_div_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    good_base_cnt: Mapped[str | None] = mapped_column(String(10), nullable=True)
    good_smlcls_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    detail_mean: Mapped[str | None] = mapped_column(String(200), nullable=True)
    good_total_cnt: Mapped[str | None] = mapped_column(String(15), nullable=True)
    good_total_div_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    product_entp_code: Mapped[str | None] = mapped_column(String(70), nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    prices: Mapped[list["ProductPrice"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductPrice(Base):
    """상품 가격 정보. 판매업소·조사일 단위 기록."""

    __tablename__ = "product_prices"
    __table_args__ = (
        Index("ix_pp_fetched_at", "fetched_at"),
        Index("ix_pp_survey_date", "survey_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    good_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("product_info.good_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    on_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    survey_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    product: Mapped["ProductInfo"] = relationship(back_populates="prices")
