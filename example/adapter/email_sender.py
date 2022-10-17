from ..port.email_sender import IEmailSender

from loguru import logger


class FakeEmailSender(IEmailSender):
    async def send(self, from_: str, to_list: list[str], title: str, body: str):
        logger.info(
            f"from: {from_}, to: {','.join(to_list)}, title: {title}, body: {body}"
        )
