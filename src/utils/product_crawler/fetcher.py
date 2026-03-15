"""한국소비자원 생필품 가격 정보 API 수집기.

API 엔드포인트:
  - getProductInfoSvc.do  — 상품 정보 조회
  - getProductPriceInfoSvc.do — 가격 정보 조회

응답: XML 기본. JSON 지원 시 &type=json 시도 후 XML 폴백.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import httpx

from src.core.config import get_settings
from src.db.session import SessionLocal

logger = logging.getLogger(__name__)

# ── 결과 데이터 ──────────────────────────────────────────────


@dataclass(slots=True)
class ProductItem:
    good_id: str
    good_name: str
    good_unit_div_code: str | None = None
    good_base_cnt: str | None = None
    good_smlcls_code: str | None = None
    detail_mean: str | None = None
    good_total_cnt: str | None = None
    good_total_div_code: str | None = None
    product_entp_code: str | None = None
    raw_data: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PriceItem:
    good_id: str
    price: int
    store_name: str | None = None
    on_sale: bool = False
    survey_date: str | None = None
    raw_data: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class FetchResult:
    fetched_at: str
    product_count: int = 0
    price_count: int = 0
    elapsed_seconds: float = 0.0
    products: list[ProductItem] = field(default_factory=list)
    prices: list[PriceItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── URL 빌더 ─────────────────────────────────────────────────


def _build_url(
    endpoint: str,
    service_key: str,
    operation: str,
    page_no: int = 1,
    num_of_rows: int = 100,
    *,
    extra_params: dict[str, str] | None = None,
) -> str:
    # 이 API는 HTTP만 지원 (HTTPS → 404)
    base = endpoint.replace("https://", "http://").rstrip("/")
    url = f"{base}/{operation}?serviceKey={service_key}&pageNo={page_no}&numOfRows={num_of_rows}"
    if extra_params:
        for k, v in extra_params.items():
            url += f"&{k}={v}"
    return url


# ── 응답 파서 ─────────────────────────────────────────────────


def _parse_xml_items(text: str) -> tuple[list[dict], int]:
    """XML 응답에서 item 리스트와 totalCount를 추출한다."""
    root = ET.fromstring(text)

    # 에러 응답 확인 — 공공데이터포털은 다양한 에러 구조를 사용함
    result_code = root.findtext(".//resultCode") or ""
    if result_code and result_code != "00":
        err_msg = (
            root.findtext(".//resultMsg")
            or root.findtext(".//errMsg")
            or root.findtext(".//returnAuthMsg")
            or "Unknown error"
        )
        raise ValueError(f"API 오류: [{result_code}] {err_msg}")

    total_count = int(root.findtext(".//totalCount") or "0")
    items: list[dict] = []
    for item in root.iter("item"):
        row: dict = {}
        for child in item:
            row[child.tag] = child.text
        items.append(row)
    return items, total_count


def _parse_response(text: str) -> tuple[list[dict], int]:
    """응답 문자열을 파싱한다. JSON 시도 → XML 폴백."""
    text = text.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            data = json.loads(text)
            body = data.get("response", data).get("body", {})
            total_count = int(body.get("totalCount", 0))
            items_wrapper = body.get("items", {})
            if isinstance(items_wrapper, dict):
                items = items_wrapper.get("item", [])
            else:
                items = items_wrapper
            if isinstance(items, dict):
                items = [items]
            return items, total_count
        except (json.JSONDecodeError, KeyError, AttributeError):
            pass

    return _parse_xml_items(text)


# ── API 호출 ──────────────────────────────────────────────────


def fetch_products(
    num_of_rows: int = 100,
    max_pages: int | None = None,
    timeout: float = 30.0,
) -> list[ProductItem]:
    """상품 정보를 페이지네이션으로 전체 수집한다."""
    settings = get_settings()
    if (
        not settings.openapi_product_price_encoding_key
        or not settings.openapi_product_price_endpoint
    ):
        raise RuntimeError(
            "OPENAPI_PRODUCT_PRICE_ENCODING_KEY / OPENAPI_PRODUCT_PRICE_ENDPOINT 환경변수를 설정하세요"
        )

    products: list[ProductItem] = []
    page_no = 1

    with httpx.Client(timeout=timeout) as client:
        while True:
            url = _build_url(
                settings.openapi_product_price_endpoint,
                settings.openapi_product_price_encoding_key,
                "getProductInfoSvc.do",
                page_no=page_no,
                num_of_rows=num_of_rows,
            )
            logger.info("상품정보 수집 page=%d url=%s", page_no, url[:120] + "...")
            resp = client.get(url)
            resp.raise_for_status()

            items, total_count = _parse_response(resp.text)
            logger.info("page=%d items=%d totalCount=%d", page_no, len(items), total_count)

            for item in items:
                products.append(
                    ProductItem(
                        good_id=item.get("goodId", ""),
                        good_name=item.get("goodName", ""),
                        good_unit_div_code=item.get("goodUnitDivCode"),
                        good_base_cnt=item.get("goodBaseCnt"),
                        good_smlcls_code=item.get("goodSmlclsCode"),
                        detail_mean=item.get("detailMean"),
                        good_total_cnt=item.get("goodTotalCnt"),
                        good_total_div_code=item.get("goodTotalDivCode"),
                        product_entp_code=item.get("productEntpCode"),
                        raw_data=json.dumps(item, ensure_ascii=False),
                    )
                )

            if not items or len(products) >= total_count:
                break
            if max_pages and page_no >= max_pages:
                break
            page_no += 1

    logger.info("상품정보 수집 완료: %d건", len(products))
    return products


def fetch_prices(
    good_id: str,
    num_of_rows: int = 100,
    max_pages: int | None = None,
    timeout: float = 30.0,
) -> list[PriceItem]:
    """특정 상품의 가격 정보를 수집한다."""
    settings = get_settings()
    prices: list[PriceItem] = []
    page_no = 1

    with httpx.Client(timeout=timeout) as client:
        while True:
            url = _build_url(
                settings.openapi_product_price_endpoint,
                settings.openapi_product_price_encoding_key,
                "getProductPriceInfoSvc.do",
                page_no=page_no,
                num_of_rows=num_of_rows,
                extra_params={"goodId": good_id},
            )
            resp = client.get(url)
            resp.raise_for_status()

            items, total_count = _parse_response(resp.text)

            for item in items:
                raw_price = item.get("goodPrice") or item.get("price") or "0"
                try:
                    price_val = int(raw_price.replace(",", ""))
                except (ValueError, AttributeError):
                    price_val = 0

                sale_flag = item.get("saleYn") or item.get("onSale") or "N"
                on_sale = sale_flag.upper() in ("Y", "YES", "TRUE", "1")

                prices.append(
                    PriceItem(
                        good_id=good_id,
                        price=price_val,
                        store_name=item.get("entpName") or item.get("storeName"),
                        on_sale=on_sale,
                        survey_date=item.get("surveyDt") or item.get("surveyDate"),
                        raw_data=json.dumps(item, ensure_ascii=False),
                    )
                )

            if not items or len(prices) >= total_count:
                break
            if max_pages and page_no >= max_pages:
                break
            page_no += 1

    return prices


# ── 메인 진입점 ───────────────────────────────────────────────


def run_fetch(
    num_of_rows: int = 100,
    max_pages: int | None = None,
    timeout: float = 30.0,
    *,
    products_only: bool = False,
) -> FetchResult:
    """상품 정보 + 가격 정보를 순차 수집한다."""
    start = time.monotonic()
    now_str = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

    products = fetch_products(num_of_rows=num_of_rows, max_pages=max_pages, timeout=timeout)

    all_prices: list[PriceItem] = []
    if not products_only:
        consecutive_failures = 0
        for i, product in enumerate(products):
            logger.info(
                "가격정보 수집 [%d/%d] goodId=%s %s",
                i + 1,
                len(products),
                product.good_id,
                product.good_name,
            )
            try:
                prices = fetch_prices(
                    product.good_id,
                    num_of_rows=num_of_rows,
                    max_pages=max_pages,
                    timeout=timeout,
                )
                all_prices.extend(prices)
                consecutive_failures = 0
            except Exception as exc:
                consecutive_failures += 1
                logger.warning("가격정보 수집 실패 goodId=%s: %s", product.good_id, exc)
                if consecutive_failures >= 3:
                    logger.warning("연속 %d건 실패, 가격 수집 중단", consecutive_failures)
                    break

    elapsed = time.monotonic() - start
    logger.info(
        "전체 수집 완료: 상품 %d건, 가격 %d건 (%.1f초)",
        len(products),
        len(all_prices),
        elapsed,
    )

    return FetchResult(
        fetched_at=now_str,
        product_count=len(products),
        price_count=len(all_prices),
        elapsed_seconds=round(elapsed, 2),
        products=products,
        prices=all_prices,
    )


# ── DB 저장 ──────────────────────────────────────────────────


def save_to_db(result: FetchResult) -> tuple[int, int]:
    """수집 결과를 DB에 저장한다. (product_saved, price_saved) 반환."""
    from sqlalchemy import select

    from src.models.pipeline import ProductInfo

    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        # 기존 good_id 세트 조회 (중복 스킵용)
        existing_ids: set[str] = set(db.scalars(select(ProductInfo.good_id)).all())

        # 상품 저장
        new_products: list[ProductInfo] = []
        for p in result.products:
            if p.good_id in existing_ids:
                continue
            new_products.append(
                ProductInfo(
                    id=str(uuid.uuid4()),
                    good_id=p.good_id,
                    good_name=p.good_name,
                    good_unit_div_code=p.good_unit_div_code,
                    good_base_cnt=p.good_base_cnt,
                    good_smlcls_code=p.good_smlcls_code,
                    detail_mean=p.detail_mean,
                    good_total_cnt=p.good_total_cnt,
                    good_total_div_code=p.good_total_div_code,
                    product_entp_code=p.product_entp_code,
                    raw_data=p.raw_data,
                    fetched_at=now,
                    created_at=now,
                )
            )
            existing_ids.add(p.good_id)

        if new_products:
            db.add_all(new_products)
            db.flush()
            logger.info("상품 %d건 신규 저장", len(new_products))

        db.commit()

    return len(new_products), 0
