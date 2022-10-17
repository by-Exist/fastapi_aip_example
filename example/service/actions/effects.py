from ..blocks import effects
from ...port.email_sender import IEmailSender


async def send_mail(eft: effects.SendMail, email_sender: IEmailSender):
    await email_sender.send(
        from_=eft.from_, to_list=[eft.to], title=eft.title, body=eft.body
    )
