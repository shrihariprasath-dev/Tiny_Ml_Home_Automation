from app.models.user import User
from app.models.device import Device
from app.models.room import Room
from app.models.schedule import Schedule
from app.models.automation_rule import AutomationRule
from app.models.alert import Alert
from app.models.ota_release import OtaRelease

__all__ = [
    "User", "Device", "Room", "Schedule",
    "AutomationRule", "Alert", "OtaRelease",
]
