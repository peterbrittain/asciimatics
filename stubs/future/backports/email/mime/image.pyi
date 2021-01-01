from future.backports.email.mime.nonmultipart import MIMENonMultipart
from typing import Any, Optional

class MIMEImage(MIMENonMultipart):
    def __init__(self, _imagedata: Any, _subtype: Optional[Any] = ..., _encoder: Any = ..., **_params: Any) -> None: ...
