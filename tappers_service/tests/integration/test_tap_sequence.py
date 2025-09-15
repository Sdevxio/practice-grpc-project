import time

from tappers_service.tapper_system.controller.tapper_service import TapperService

class TestTapperService:

    def test_tap_sequence(self):
        # Use HTTP-only station to avoid MQTT fallback issues
        service = TapperService("station1")

        service.connect()

        sequences.safe_tap_card2(service.protocol)
        time.sleep(2)
        sequences.safe_tap_card1(service.protocol)


