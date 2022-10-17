from typing import Protocol


class IEmailSender(Protocol):
    async def send(self, from_: str, to_list: list[str], title: str, body: str):
        ...