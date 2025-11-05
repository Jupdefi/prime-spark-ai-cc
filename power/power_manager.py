"""
Power Management System
Handles on-grid vs off-grid operation modes with battery monitoring
"""
import asyncio
import psutil
from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from config.settings import settings


class PowerMode(Enum):
    """Power operation modes"""
    ON_GRID = "on-grid"
    OFF_GRID = "off-grid"
    AUTO = "auto"


class BatteryState(Enum):
    """Battery charge states"""
    FULL = "full"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PowerStatus:
    """Current power status"""
    mode: PowerMode
    is_on_battery: bool
    battery_percent: Optional[float]
    battery_state: BatteryState
    time_remaining: Optional[int]  # minutes
    power_plugged: bool
    edge_only_mode: bool
    timestamp: datetime


class PowerManager:
    """
    Manages power states and adjusts system behavior.

    Features:
    - Battery monitoring
    - Automatic mode switching
    - Power-aware routing decisions
    - Graceful degradation on low battery
    """

    def __init__(self):
        self.mode = PowerMode[settings.power.mode.upper().replace("-", "_")]
        self.battery_monitor_enabled = settings.power.battery_monitor_enabled
        self.battery_low_threshold = settings.power.battery_low_threshold
        self.battery_critical_threshold = settings.power.battery_critical_threshold

        self._current_status: Optional[PowerStatus] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start power monitoring"""
        if self.battery_monitor_enabled:
            self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop power monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    def _get_battery_info(self) -> tuple[bool, Optional[float], Optional[int], bool]:
        """
        Get battery information from system.

        Returns:
            (is_on_battery, battery_percent, time_remaining_minutes, power_plugged)
        """
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                # No battery detected (desktop system)
                return False, None, None, True

            is_on_battery = not battery.power_plugged
            battery_percent = battery.percent
            time_remaining = int(battery.secsleft / 60) if battery.secsleft > 0 else None
            power_plugged = battery.power_plugged

            return is_on_battery, battery_percent, time_remaining, power_plugged

        except Exception as e:
            print(f"Error getting battery info: {e}")
            return False, None, None, True

    def _determine_battery_state(self, battery_percent: Optional[float]) -> BatteryState:
        """Determine battery state from percentage"""
        if battery_percent is None:
            return BatteryState.UNKNOWN

        if battery_percent >= 95:
            return BatteryState.FULL
        elif battery_percent >= 70:
            return BatteryState.HIGH
        elif battery_percent >= self.battery_low_threshold:
            return BatteryState.NORMAL
        elif battery_percent >= self.battery_critical_threshold:
            return BatteryState.LOW
        else:
            return BatteryState.CRITICAL

    def _should_use_edge_only(
        self,
        is_on_battery: bool,
        battery_state: BatteryState
    ) -> bool:
        """Determine if system should operate in edge-only mode"""
        if not is_on_battery:
            return False

        # Critical battery: edge only
        if battery_state == BatteryState.CRITICAL:
            return True

        # Low battery: edge only
        if battery_state == BatteryState.LOW:
            return True

        return False

    async def get_power_status(self) -> PowerStatus:
        """Get current power status"""
        is_on_battery, battery_percent, time_remaining, power_plugged = self._get_battery_info()

        battery_state = self._determine_battery_state(battery_percent)
        edge_only_mode = self._should_use_edge_only(is_on_battery, battery_state)

        status = PowerStatus(
            mode=self.mode,
            is_on_battery=is_on_battery,
            battery_percent=battery_percent,
            battery_state=battery_state,
            time_remaining=time_remaining,
            power_plugged=power_plugged,
            edge_only_mode=edge_only_mode,
            timestamp=datetime.now()
        )

        self._current_status = status
        return status

    async def get_routing_mode(self) -> Literal["on-grid", "off-grid"]:
        """
        Get current routing mode for request routing.

        Returns:
            "on-grid" or "off-grid"
        """
        status = await self.get_power_status()

        # Manual mode override
        if self.mode == PowerMode.ON_GRID:
            return "on-grid"
        elif self.mode == PowerMode.OFF_GRID:
            return "off-grid"

        # Auto mode
        if status.edge_only_mode or status.is_on_battery:
            return "off-grid"
        else:
            return "on-grid"

    async def set_mode(self, mode: PowerMode):
        """Set power mode manually"""
        self.mode = mode
        print(f"Power mode set to: {mode.value}")

    async def _monitor_loop(self):
        """Monitor power status and trigger events"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                status = await self.get_power_status()

                # Log state changes
                if self._current_status:
                    if status.battery_state != self._current_status.battery_state:
                        await self._on_battery_state_changed(status)

                    if status.is_on_battery != self._current_status.is_on_battery:
                        await self._on_power_source_changed(status)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in power monitor loop: {e}")

    async def _on_battery_state_changed(self, status: PowerStatus):
        """Handle battery state change"""
        print(f"Battery state changed: {status.battery_state.value}")

        if status.battery_state == BatteryState.CRITICAL:
            print("WARNING: Battery critical! Switching to edge-only mode.")
            await self._enable_power_saving()

        elif status.battery_state == BatteryState.LOW:
            print("WARNING: Battery low! Consider connecting to power.")

    async def _on_power_source_changed(self, status: PowerStatus):
        """Handle power source change"""
        if status.is_on_battery:
            print("Power disconnected: Running on battery")
            if self.mode == PowerMode.AUTO:
                print("Switching to edge-first mode to conserve power")
        else:
            print("Power connected: Charging")
            if self.mode == PowerMode.AUTO:
                print("Full capabilities restored")
                await self._disable_power_saving()

    async def _enable_power_saving(self):
        """Enable power-saving measures"""
        # TODO: Implement power-saving measures:
        # - Reduce background tasks
        # - Lower refresh rates
        # - Disable non-essential services
        # - Prioritize edge compute
        print("Power-saving mode enabled")

    async def _disable_power_saving(self):
        """Disable power-saving measures"""
        # TODO: Restore normal operation
        print("Power-saving mode disabled")

    async def get_power_stats(self) -> dict:
        """Get power statistics"""
        status = await self.get_power_status()

        return {
            "mode": self.mode.value,
            "is_on_battery": status.is_on_battery,
            "battery_percent": status.battery_percent,
            "battery_state": status.battery_state.value,
            "time_remaining_minutes": status.time_remaining,
            "power_plugged": status.power_plugged,
            "edge_only_mode": status.edge_only_mode,
            "routing_mode": await self.get_routing_mode(),
            "timestamp": status.timestamp.isoformat()
        }


# Global power manager instance
power_manager = PowerManager()
