from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from aip.filter import Converter as FilterConverter
from aip.order_by import Converter as OrderByConverter
from aip.page import Cursor, PageToken, get_page_clause
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy import and_, desc, not_, or_, select

from ..adapter.unit_of_work import UnitOfWork
from ..bootstrap import bootstrap
from ..domain.book import Book
from ..service.blocks import commands as blocks

app = FastAPI()
domino = bootstrap(start_orm_mapper=True, Uow=UnitOfWork)


async def create_test_resource():
    # create publisher
    publisher_id = uuid4()
    await domino.start(blocks.CreatePublisher(id=publisher_id, title="무궁화출판사"))
    # create publishser's books
    await domino.start(
        blocks.CreateBook(
            id=uuid4(),
            publisher_id=publisher_id,
            title="동해물과",
            author_name="작가명",
            publish_time=datetime.now(),
        )
    )
    await domino.start(
        blocks.CreateBook(
            id=uuid4(),
            publisher_id=publisher_id,
            title="백두산이",
            author_name="작가명",
            publish_time=datetime.now(),
        )
    )
    await domino.start(
        blocks.CreateBook(
            id=uuid4(),
            publisher_id=publisher_id,
            title="마르고",
            author_name="작가명",
            publish_time=datetime.now(),
        )
    )
    await domino.start(
        blocks.CreateBook(
            id=uuid4(),
            publisher_id=publisher_id,
            title="닳도록",
            author_name="작가명",
            publish_time=datetime.now(),
        )
    )


@app.on_event("startup")  # type: ignore
async def startup():
    from ..adapter.orm import mapper_registry
    from ..adapter.unit_of_work import engine

    async with engine.connect() as conn:
        await conn.run_sync(mapper_registry.metadata.create_all)
        await conn.commit()

    await create_test_resource()


#
# Get Publisher
#
class PublisherResponse(BaseModel):

    id: UUID
    title: str

    class Config:
        orm_mode = True


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


#
# Create Publisher
#
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


#
# Fix Publisher Title
#
class FixPublisherTitleRequest(BaseModel):
    new_title: str


@app.post(
    "/publishers/{publisher_id}:fixTitle",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["Publisher"],
)
async def fix_title_publisher(publisher_id: UUID, req: FixPublisherTitleRequest):
    await domino.start(
        blocks.FixPublisherTitle(id=publisher_id, new_title=req.new_title)
    )


#
# Get Book
#
WILDCARD_COLLECTION_ID = "-"
WILDCARD_COLLECTION_ID_TYPE = Literal["-"]


class BookResponse(BaseModel):

    id: UUID
    publisher_id: UUID

    title: str
    author_name: str
    publish_time: datetime

    class Config:
        orm_mode = True


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
    async with UnitOfWork() as uow:
        book = await uow.books.get(book_id)
        assert book
        if publisher_id != WILDCARD_COLLECTION_ID:
            assert book.publisher_id == publisher_id
    return book


#
# Create Book
#
class CreateBookRequest(BaseModel):
    title: str
    author_name: str
    publish_time: datetime


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
            publish_time=req.publish_time,
        ),
    )
    async with UnitOfWork() as uow:
        book = await uow.books.get(book_id)
    assert book
    return BookResponse.from_orm(book)


#
# Search Books
#
DEFAULT_PAGE_SIZE = 30
DEFAULT_ORDER_BY = [Book.publish_time]


class ListBooksResponse(BaseModel):
    books: list[BookResponse]
    next_page_token: str


filter_converter = FilterConverter(
    objects={"book": Book},
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
    publish_time: datetime


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
                publish_time=books[-1].publish_time,
            ),
        ).encode()
        if next_page_book
        else ""
    )

    return {"books": books, "next_page_token": next_page_token}


#
# Delete Book
#
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
