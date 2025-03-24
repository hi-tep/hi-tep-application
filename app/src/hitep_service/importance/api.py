from dataclasses import dataclass
from typing import List, Tuple

from build.lib.cltl.commons.discrete import UtteranceType


@dataclass
class Source:
    label: str
    type: List[str]
    uri: str


@dataclass
class Entity:
    label: str
    type: List[str]
    id: str
    uri: str

    @classmethod
    def create_person(cls, label: str, id_: str, uri: str):
        return cls(label, ["person"], id_, uri)


@dataclass
class PaintingExperience:
    visual: str
    detection: str
    source: Source
    image: str
    region: Tuple[int, int, int, int]
    item: Entity
    confidence: float
    context_id: str
    timestamp: int
    utterance_type: UtteranceType = UtteranceType.EXPERIENCE
