import asyncio
from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from aip.filter import Converter as FilterConverter
from aip.order_by import Converter as OrderByConverter
from aip.page import Cursor, PageToken, get_page_clause
from fastapi import FastAPI, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, not_, or_, select

from ..adapter.unit_of_work import UnitOfWork
from ..bootstrap import bootstrap
from ..domain.book import Book
from ..domain.publisher import Publisher
from ..service.blocks import commands as blocks


app = FastAPI(
    title="FastAPI AIP Example",
    description="Google에서 공개한 [AIP](https://google.aip.dev/)에 등장하는 API 설계 패턴들을 FastAPI를 통해 구현한 예제입니다.",
)
domino = bootstrap(start_orm_mapper=True, Uow=UnitOfWork)


async def create_test_resource():
    # create publisher

    create_publisher_blocks: list[blocks.CreatePublisher] = []
    create_book_blocks: list[blocks.CreateBook] = []

    문학동네_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=문학동네_id, title="문학동네"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=문학동네_id, title="변신", author_name="프란츠 카프카"
        )
    )
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=문학동네_id, title="소송", author_name="프란츠 카프카"
        )
    )

    워크룸프레스_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=워크룸프레스_id, title="워크룸프레스"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=워크룸프레스_id, title="꿈", author_name="프란츠 카프카"
        )
    )

    창비_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=창비_id, title="창비"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=창비_id, title="성", author_name="프란츠 카프카"
        )
    )

    솔출판사_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=솔출판사_id, title="솔출판사"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=솔출판사_id, title="어느 개의 연구", author_name="프란츠 카프카"
        )
    )

    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=문학동네_id, title="노인과 바다", author_name="어니스트 헤밍웨이"
        )
    )

    이숲_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=이숲_id, title="이숲"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=이숲_id, title="파리는 날마다 축제", author_name="어니스트 헤밍웨이"
        )
    )

    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=문학동네_id, title="킬리만자로의 눈", author_name="어니스트 헤밍웨이"
        )
    )

    열린책들_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=열린책들_id, title="열린책들"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(),
            publisher_id=열린책들_id,
            title="누구를 위하여 종은 울리나",
            author_name="어니스트 헤밍웨이",
        )
    )

    민음사_id = uuid4()
    create_publisher_blocks.append(blocks.CreatePublisher(id=민음사_id, title="민음사"))
    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=민음사_id, title="동물농장", author_name="조지 오웰"
        )
    )

    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=민음사_id, title="1984", author_name="조지 오웰"
        )
    )

    create_book_blocks.append(
        blocks.CreateBook(
            id=uuid4(), publisher_id=민음사_id, title="카탈로니아 찬가", author_name="조지 오웰"
        )
    )

    await asyncio.gather(*(domino.start(block) for block in create_publisher_blocks))
    await asyncio.gather(*(domino.start(block) for block in create_book_blocks))


@app.on_event("startup")  # type: ignore
async def startup():
    from ..adapter.orm import mapper_registry
    from ..adapter.unit_of_work import engine

    async with engine.connect() as conn:
        await conn.run_sync(mapper_registry.metadata.create_all)
        await conn.commit()

    await create_test_resource()


# =========================================================
# Global
# =========================================================
WILDCARD_COLLECTION_ID = "-"
WILDCARD_COLLECTION_ID_TYPE = Literal["-"]


# =========================================================
# Book
# =========================================================
class PublisherResponse(BaseModel):

    id: UUID = Field(..., description="출판사 id")
    title: str = Field(..., description="출판사 이름")

    class Config:
        orm_mode = True


class ListPublisherResponse(BaseModel):

    publishers: list[PublisherResponse]
    next_page_token: str


# ========== List ==========
DEFAULT_PUBLISHER_ORDER_BY = [Publisher.title]
DEFAULT_PUBLISHER_PAGE_SIZE = 30


class PublisherCursor(Cursor):
    id: UUID
    title: str


@app.get(
    "/publishers",
    response_model=ListPublisherResponse,
    tags=["Publisher"],
)
async def list_publishers(
    page_size: int | None,
    page_token: str | None,
    skip: int | None,
):
    """
    - 다음 페이지가 존재할 경우 응답에 **next_page_token** 문자열 토큰이 포함됩니다.
    - **page_token**에 이전 응답의 next_page_token을 입력할 경우 다음 페이지를 반환합니다.
    - **skip**을 입력할 경우 해당 갯수 만큼의 리소스를 skip한 뒤 페이징합니다.
    """
    token = None
    if page_token:
        token = PageToken[BookCursor].decode(page_token)
    order_by_clauses = DEFAULT_PUBLISHER_ORDER_BY
    page_clause = get_page_clause(order_by_clauses, token.cursor) if token else None
    limit = page_size if page_size else DEFAULT_PUBLISHER_PAGE_SIZE
    offset = skip if skip else None

    stat = select(Publisher)
    if page_clause is not None:
        stat = stat.where(page_clause)
    stat = stat.order_by(*order_by_clauses)
    if limit:
        stat = stat.limit(limit + 1)
    if offset:
        stat = stat.offset(offset)

    async with UnitOfWork() as uow:
        publishers = await uow.publishers.query(stat)

    next_page_book = publishers.pop() if len(publishers) > limit else None
    next_page_token = (
        PageToken(
            filter_query=None,
            order_by_query=None,
            cursor=PublisherCursor(
                id=publishers[-1].id,
                title=publishers[-1].title,
            ),
        ).encode()
        if next_page_book
        else ""
    )

    return {"publishers": publishers, "next_page_token": next_page_token}


# ========== Create ==========
class CreatePublisherRequest(BaseModel):
    title: str


@app.post(
    "/publishers",
    response_model=PublisherResponse,
    tags=["Publisher"],
)
async def create_publisher(req: CreatePublisherRequest):
    publisher_id = uuid4()
    await domino.start(blocks.CreatePublisher(id=publisher_id, title=req.title))
    async with UnitOfWork() as uow:
        publisher = await uow.publishers.get(publisher_id)
    return PublisherResponse.from_orm(publisher)


# ========== Get ==========
@app.get(
    "/publishers/{publisher_id}",
    status_code=status.HTTP_200_OK,
    response_model=PublisherResponse,
    tags=["Publisher"],
)
async def get_publisher(publisher_id: UUID):
    async with UnitOfWork() as uow:
        publisher = await uow.publishers.get(publisher_id)
    assert publisher
    return publisher


# =========================================================
# Book
# =========================================================
class BookResponse(BaseModel):

    id: UUID
    publisher_id: UUID

    title: str
    author_name: str

    class Config:
        orm_mode = True


class ListBooksResponse(BaseModel):
    books: list[BookResponse]
    next_page_token: str


# ========== Craete ==========
class CreateBookRequest(BaseModel):
    title: str
    author_name: str


@app.post(
    "/publishers/{publisher_id}/books",
    response_model=BookResponse,
    tags=["Book"],
)
async def create_book(publisher_id: UUID, req: CreateBookRequest):
    async with UnitOfWork() as uow:
        assert await uow.publishers.get(publisher_id)
    book_id = uuid4()
    await domino.start(
        blocks.CreateBook(
            id=book_id,
            publisher_id=publisher_id,
            title=req.title,
            author_name=req.author_name,
        ),
    )
    async with UnitOfWork() as uow:
        book = await uow.books.get(book_id)
    assert book
    return BookResponse.from_orm(book)


# ========== Search ==========
DEFAULT_PAGE_SIZE = 30
DEFAULT_ORDER_BY = [Book.title]


def contains(c: Any, v: str):
    return c.contains(v)


def in_(c: Any, *vs: Any):
    return c.in_(vs)


filter_converter = FilterConverter(
    objects={"book": Book, "contains": contains, "in": in_},
    not_=not_,
    and_=and_,
    or_=or_,
)

order_by_converter = OrderByConverter(
    objects={"book": Book},
    desc=desc,
)


class BookCursor(Cursor):
    title: str
    author_name: str


@app.get(
    "/publishers/{publisher_id}/books:search",
    response_model=ListBooksResponse,
    tags=["Book"],
)
async def search_books(
    publisher_id: UUID | WILDCARD_COLLECTION_ID_TYPE,
    filter: str | None = None,
    order_by: str | None = None,
    page_size: int | None = None,
    page_token: str | None = None,
    skip: int | None = None,
):
    """
    - **publisher_id**를 지정할 경우 해당 퍼블리셔의 book들로 응답을 제한합니다.
        - publisher_id를 collection wildcard id인 "-"로 지정하여 제한하지 않을 수 있습니다.
    - [**filter** 문법](https://google.aip.dev/160)을 활용하여 원하는 books만을 조회할 수 있습니다.
        - 사용 가능한 필드
            - book.title
            - book.author_name
        - 사용 가능한 함수
            - contains(field, str) - 대소문자 구분 없이 field 내에 str의 포함 여부
            - in(field, *values) - field가 values 내에 있는지의 여부
        - 예제
            - book.title = "동물농장" AND book.author_name = "조지 오웰"
            - contains(book.author_name, "카프카")
            - in(book.author_name, "어니스트 헤밍웨이", "프란츠 카프카")
    - [**order_by** 문법](https://cloud.google.com/monitoring/api/v3/sorting-and-filtering#sort-order_syntax)을 활용하여 원하는 방식으로 정렬할 수 있습니다.
        - 사용 가능한 필드
            - book.title
            - book.author_name
        - 에제
            - book.title desc
            - book.author_name, book.title desc
    - 다음 페이지가 존재할 경우 응답에 **next_page_token** 문자열 토큰이 포함됩니다.
    - **page_token**에 이전 응답의 next_page_token을 입력할 경우 다음 페이지를 반환합니다.
    - **skip**을 입력할 경우 해당 갯수 만큼의 리소스를 skip한 뒤 페이징합니다.
    """
    token = None
    if page_token:
        token = PageToken[BookCursor].decode(page_token)
        assert token.filter_query == filter
        assert token.order_by_query == order_by

    publisher_clause = (
        Book.publisher_id == publisher_id
        if publisher_id != WILDCARD_COLLECTION_ID
        else None
    )
    filter_clause = filter_converter.convert(filter) if filter else None
    order_by_clauses = (
        order_by_converter.convert(order_by) if order_by else DEFAULT_ORDER_BY
    )
    page_clause = get_page_clause(order_by_clauses, token.cursor) if token else None
    limit = page_size if page_size else DEFAULT_PAGE_SIZE
    offset = skip if skip else None

    stat = select(Book)
    if publisher_clause is not None:
        stat = stat.where(publisher_clause)
    if filter_clause is not None:
        stat = stat.where(filter_clause)
    if page_clause is not None:
        stat = stat.where(page_clause)
    stat = stat.order_by(*order_by_clauses)
    if limit:
        stat = stat.limit(limit + 1)
    if offset:
        stat = stat.offset(offset)

    async with UnitOfWork() as uow:
        books = await uow.books.query(stat)

    next_page_book = books.pop() if len(books) > limit else None
    next_page_token = (
        PageToken(
            filter_query=filter,
            order_by_query=order_by,
            cursor=BookCursor(
                title=books[-1].title,
                author_name=books[-1].author_name,
            ),
        ).encode()
        if next_page_book
        else ""
    )

    return {"books": books, "next_page_token": next_page_token}


# ========== Get ==========
@app.get(
    "/publishers/{publisher_id}/books/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=BookResponse,
    tags=["Book"],
)
async def get_book(
    publisher_id: UUID | Literal[WILDCARD_COLLECTION_ID_TYPE],
    book_id: UUID,
):
    """
    - publisher_id는 **collection wildcard id**인 "-"를 입력함으로써 생략할 수 있습니다.
    """
    async with UnitOfWork() as uow:
        book = await uow.books.get(book_id)
        assert book
        if publisher_id != WILDCARD_COLLECTION_ID:
            assert book.publisher_id == publisher_id
    return book


# ========== Delete ==========
@app.delete(
    "/publishers/{publisher_id}/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Book"],
)
async def delete_book(publisher_id: UUID, book_id: UUID):
    async with UnitOfWork() as uow:
        book = await uow.books.get(book_id)
        assert book
        assert book.publisher_id == publisher_id
    await domino.start(blocks.DeleteBook(id=book_id))
