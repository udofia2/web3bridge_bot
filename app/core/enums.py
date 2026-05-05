from enum import Enum


class TopicMode(str, Enum):
    NORMAL = "normal"
    ANNOUNCEMENT = "announcement"
    RESTRICTED = "restricted"
