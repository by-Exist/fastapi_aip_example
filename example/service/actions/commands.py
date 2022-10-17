from datetime import datetime
from domino.domino import touch

from ...domain.publisher import Publisher
from ...domain.book import Book
from ...port.unit_of_work import IUnitOfWork
from ..blocks import commands, events


async def create_publisher(cmd: commands.CreatePublisher, Uow: type[IUnitOfWork]):
    publisher = Publisher(id=cmd.id, title=cmd.title)
    async with Uow() as uow:
        await uow.publishers.add(publisher)
        await uow.commit()
    touch(events.PublisherCreated(id=cmd.id))


async def fix_publisher_title(cmd: commands.FixPublisherTitle, Uow: type[IUnitOfWork]):
    async with Uow() as uow:
        publisher = await uow.publishers.get(cmd.id)
        assert publisher
        publisher.title = cmd.new_title
        await uow.commit()
    touch(events.PublisherTitleFixed(id=publisher.id))


async def create_book(cmd: commands.CreateBook, Uow: type[IUnitOfWork]):
    book = Book(
        id=cmd.id,
        publisher_id=cmd.publisher_id,
        title=cmd.title,
        author_name=cmd.author_name,
        publish_time=datetime.now(),
    )
    async with Uow() as uow:
        await uow.books.add(book)
        await uow.commit()
    touch(events.BookCreated(id=cmd.id))


async def delete_book(cmd: commands.DeleteBook, Uow: type[IUnitOfWork]):
    async with Uow() as uow:
        book = await uow.books.get(cmd.id)
        assert book
        await uow.books.delete(book)
        await uow.commit()
    touch(events.BookDeleted(id=cmd.id))
