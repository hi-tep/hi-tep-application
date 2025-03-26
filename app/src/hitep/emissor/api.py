import uuid
from typing import Iterable, Any
from typing import Optional

from emissor.representation.container import AtomicContainer, AtomicRuler, TemporalRuler
from emissor.representation.ldschema import emissor_dataclass
from emissor.representation.scenario import Signal, Mention, Modality
from emissor.representation.util import Identifier

from hitep.openapi_server.models.gaze_detection import GazeDetection
from hitep.openapi_server.models.position_change import PositionChange


@emissor_dataclass
class PositionSignal(Signal[AtomicRuler, PositionChange], AtomicContainer[PositionChange]):
    @classmethod
    def for_scenario(cls: Any, scenario_id: Identifier, detection: PositionChange = None,
                     mentions: Iterable[Mention] = None, signal_id: Optional[str] = None):
        signal_id = signal_id if signal_id else str(uuid.uuid4())

        timestamp = int(detection.timestamp.timestamp() * 1000) if detection.timestamp else None

        return cls(signal_id, AtomicRuler(signal_id), detection.to_dict(), Modality.VIDEO, TemporalRuler(scenario_id, timestamp, timestamp),
                   [], list(mentions) if mentions else [])


@emissor_dataclass
class GazeSignal(Signal[AtomicRuler, GazeDetection], AtomicContainer[GazeDetection]):
    pass

@emissor_dataclass
class GazeStartSignal(GazeSignal):
    @classmethod
    def for_scenario(cls: Any, scenario_id: Identifier, detection: GazeDetection = None,
                     mentions: Iterable[Mention] = None, signal_id: Optional[str] = None):
        signal_id = signal_id if signal_id else str(uuid.uuid4())

        start = int(detection.start.timestamp() * 1000)

        return cls(signal_id, AtomicRuler(signal_id), detection.to_dict(), Modality.VIDEO, TemporalRuler(scenario_id, start, start),
                   [], list(mentions) if mentions else [])


@emissor_dataclass
class GazeEndSignal(GazeSignal):
    @classmethod
    def for_scenario(cls: Any, scenario_id: Identifier, detection: GazeDetection = None,
                     mentions: Iterable[Mention] = None, signal_id: Optional[str] = None):
        signal_id = signal_id if signal_id else str(uuid.uuid4())

        start = int(detection.end.timestamp() * 1000)

        return cls(signal_id, AtomicRuler(signal_id), detection.to_dict(), Modality.VIDEO, TemporalRuler(scenario_id, start, start),
                   [], list(mentions) if mentions else [])


# TODO Convert to signals for each entity
# @dataclass
# class GazeSignalStarted(SignalStarted[GazeSignal]):
#     @classmethod
#     def create(cls, signal: GazeSignal):
#         return cls(cls.__name__, Modality.VIDEO, signal)
#
#
# @dataclass
# class GazeSignalStopped(SignalStopped[GazeSignal]):
#     @classmethod
#     def create(cls, signal: GazeSignal):
#         return cls(cls.__name__, Modality.VIDEO, signal)
