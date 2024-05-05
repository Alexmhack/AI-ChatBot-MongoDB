from uuid import uuid4

from datetime import datetime
from pytz import timezone


def create_st_session_id() -> str:
    return f"{uuid4().hex} - {datetime.now(timezone('Asia/Calcutta'))}"


def create_id() -> str:
    return uuid4().hex
