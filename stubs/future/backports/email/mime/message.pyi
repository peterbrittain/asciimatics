from future.backports.email.mime.nonmultipart import MIMENonMultipart
from typing import Any

class MIMEMessage(MIMENonMultipart):
    def __init__(self, _msg: Any, _subtype: str = ...) -> None: ...
