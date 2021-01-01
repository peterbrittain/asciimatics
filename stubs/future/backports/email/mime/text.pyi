from future.backports.email.mime.nonmultipart import MIMENonMultipart
from typing import Any, Optional

class MIMEText(MIMENonMultipart):
    def __init__(self, _text: Any, _subtype: str = ..., _charset: Optional[Any] = ...) -> None: ...
