from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class CaffeineEvent:
    id: str
    timestamp: datetime
    mg: float
    label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'mg': self.mg,
            'label': self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'CaffeineEvent':
        ts = datetime.fromisoformat(data['timestamp'])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return cls(
            id=data['id'],
            timestamp=ts,
            mg=float(data['mg']),
            label=data.get('label', 'unknown'),
        )

@dataclass
class MedicineEvent:
    id: str
    name: str
    med_type: str
    timestamp: datetime
    reminder_time: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'med_type': self.med_type,
            'timestamp': self.timestamp.isoformat(),
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'MedicineEvent':
        ts = datetime.fromisoformat(data['timestamp'])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        rm = None
        if data.get('reminder_time'):
            rm = datetime.fromisoformat(data['reminder_time'])
            if rm.tzinfo is None:
                rm = rm.replace(tzinfo=timezone.utc)
        return cls(
            id=data['id'],
            name=data['name'],
            med_type=data.get('med_type', 'general'),
            timestamp=ts,
            reminder_time=rm,
        )

@dataclass
class CaffeineData:
    current_mg: float
    consumed_today_mg: float
    consumed_today_count: int
    sleep_safe_at: datetime | None
    peak_mg: float | None = None
    events: list[CaffeineEvent] = field(default_factory=list)
    water_total: float = 0.0
    drinks_total: dict[str, float] = field(default_factory=dict)
    alcohol_events: list[CaffeineEvent] = field(default_factory=list)
    medicines: list[MedicineEvent] = field(default_factory=list)
    caffeine_history: list[dict[str, Any]] = field(default_factory=list)
    current_bac: float = 0.0
    drive_safe_at: datetime | None = None
    aggregated_heart_rate: float | None = None
    aggregated_steps: int = 0
    last_drink_time: datetime | None = None

