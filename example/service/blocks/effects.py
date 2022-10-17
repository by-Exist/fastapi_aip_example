from dataclasses import dataclass
from domino.block import IBlock


@dataclass(frozen=True, kw_only=True)
class SendMail(IBlock):
    from_: str = "admin@example.com"
    to: str
    title: str
    body: str
