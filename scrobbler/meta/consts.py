from enum import Enum


class SYNC_META(Enum):
    DO_NOT_SYNC = 0
    INSERT_ONLY = 1
    INSERT_OR_UPDATE = 2
