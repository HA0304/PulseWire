import csv
import io
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .sender import SenderTracePoint


class CongestionTraceRecorder:
    def __init__(self):
        self._points: list[SenderTracePoint] = []

    @property
    def points(self) -> tuple[SenderTracePoint, ...]:
        return tuple(self._points)

    def record(self, point: SenderTracePoint) -> None:
        self._points.append(point)

    def to_csv(self) -> str:
        output = io.StringIO()
        fieldnames = ["time", "event", "cwnd", "ssthresh", "duplicate_ack_count"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(point) for point in self._points)
        return output.getvalue()

    def write_csv(self, path: str | Path) -> None:
        Path(path).write_text(self.to_csv(), encoding="utf-8")


def record_events(
    sender: "TCPSender",
    events: Iterable["CongestionEvent"],
) -> CongestionTraceRecorder:
    recorder = CongestionTraceRecorder()
    for event in events:
        recorder.record(sender.process(event))
    return recorder
