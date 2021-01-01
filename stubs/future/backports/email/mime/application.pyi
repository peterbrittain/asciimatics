from future.backports.email.mime.nonmultipart import MIMENonMultipart
from typing import Any

class MIMEApplication(MIMENonMultipart):
    def __init__(self, _data: Any, _subtype: str = ..., _encoder: Any = ..., **_params: Any) -> None: ...
