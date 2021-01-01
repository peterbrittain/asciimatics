from typing import Any

def message_from_string(s: Any, *args: Any, **kws: Any): ...
def message_from_bytes(s: Any, *args: Any, **kws: Any): ...
def message_from_file(fp: Any, *args: Any, **kws: Any): ...
def message_from_binary_file(fp: Any, *args: Any, **kws: Any): ...

# Names in __all__ with no definition:
#   base64mime
#   charset
#   encoders
#   errors
#   feedparser
#   generator
#   header
#   iterators
#   message
#   mime
#   parser
#   quoprimime
#   utils
