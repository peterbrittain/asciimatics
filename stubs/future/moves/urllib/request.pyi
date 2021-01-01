from urllib.request import *
from future.standard_library import suspend_hooks as suspend_hooks
from future.utils import PY3 as PY3
from urllib.parse import splitattr as splitattr, splithost as splithost, splitpasswd as splitpasswd, splitport as splitport, splitquery as splitquery, splittag as splittag, splittype as splittype, splituser as splituser, splitvalue as splitvalue, to_bytes as to_bytes, unwrap as unwrap
from urllib.request import getproxies as getproxies, pathname2url as pathname2url, proxy_bypass as proxy_bypass, quote as quote, request_host as request_host, thishost as thishost, unquote as unquote, url2pathname as url2pathname, urlcleanup as urlcleanup, urljoin as urljoin, urlopen as urlopen, urlparse as urlparse, urlretrieve as urlretrieve, urlsplit as urlsplit, urlunparse as urlunparse
