from domino.domino import touch
from loguru import logger

from ..blocks import events, effects


async def publisher_created(evt: events.PublisherCreated):
    logger.info(f"publisher created. (id={evt.id})")


async def publisher_title_fixed(evt: events.PublisherTitleFixed):
    logger.info(f"publisher's title fixed. (id={evt.id})")


async def book_created(evt: events.BookCreated):
    logger.info(f"book created. (id={evt.id}")
    touch(
        effects.SendMail(
            from_="admin@example.com",
            to="client",
            title="Book Created!",
            body=f"book's id is {evt.id}",
        )
    )


async def book_deleted(evt: events.BookDeleted):
    logger.info(f"book deleted. (id={evt.id}")
