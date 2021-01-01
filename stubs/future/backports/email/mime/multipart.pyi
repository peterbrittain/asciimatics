from future.backports.email.mime.base import MIMEBase
from typing import Any, Optional

class MIMEMultipart(MIMEBase):
    def __init__(self, _subtype: str = ..., boundary: Optional[Any] = ..., _subparts: Optional[Any] = ..., **_params: Any) -> None: ...
