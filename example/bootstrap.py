from domino.domino import Domino

from .adapter.email_sender import FakeEmailSender
from .adapter.orm import start_mappers
from .port.email_sender import IEmailSender
from .port.unit_of_work import IUnitOfWork
from .service.actions import commands as cmd_actions
from .service.actions import effects as eft_actions
from .service.actions import events as evt_actions
from .service.blocks import commands as cmd_blocks
from .service.blocks import effects as eft_blokcs
from .service.blocks import events as evt_blocks


def bootstrap(
    *,
    start_orm_mapper: bool,
    Uow: type[IUnitOfWork],
    email_sender: IEmailSender = FakeEmailSender()
) -> Domino:
    if start_orm_mapper:
        start_mappers()

    # Domino
    domino = Domino()
    # Commands
    domino.place(
        cmd_blocks.CreatePublisher, cmd_actions.create_publisher, Uow=Uow
    )
    domino.place(
        cmd_blocks.FixPublisherTitle, cmd_actions.fix_publisher_title, Uow=Uow
    )
    domino.place(cmd_blocks.CreateBook, cmd_actions.create_book, Uow=Uow)
    domino.place(cmd_blocks.DeleteBook, cmd_actions.delete_book, Uow=Uow)
    # Events
    domino.place(evt_blocks.PublisherCreated, evt_actions.publisher_created)
    domino.place(evt_blocks.PublisherTitleFixed, evt_actions.publisher_title_fixed)
    domino.place(evt_blocks.BookCreated, evt_actions.book_created)
    domino.place(evt_blocks.BookDeleted, evt_actions.book_deleted)
    # Effects
    domino.place(
        eft_blokcs.SendMail, eft_actions.send_mail, email_sender=email_sender
    )

    return domino
