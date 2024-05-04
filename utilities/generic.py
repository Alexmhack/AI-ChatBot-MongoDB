import uuid


def create_id() -> str:
    return uuid.uuid4().hex
