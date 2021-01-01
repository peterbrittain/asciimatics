from future.backports.email import message
from typing import Any

class MIMEBase(message.Message):
    def __init__(self, _maintype: Any, _subtype: Any, **_params: Any) -> None: ...
