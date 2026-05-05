import re


INVITE_PATTERN = re.compile(r"(t\.me/joinchat|t\.me/\+|telegram\.me/joinchat)", re.I)
URL_PATTERN = re.compile(r"https?://\S+", re.I)
