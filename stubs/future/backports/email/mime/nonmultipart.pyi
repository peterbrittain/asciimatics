from future.backports.email.mime.base import MIMEBase
from typing import Any

class MIMENonMultipart(MIMEBase):
    def attach(self, payload: Any) -> None: ...
