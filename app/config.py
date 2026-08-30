"""
Application settings
"""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

TITLE_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 1000
COMMENT_MAX_LENGTH = 1000