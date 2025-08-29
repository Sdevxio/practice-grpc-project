import time

from tappers_service.command import sequences
from tappers_service.controller.tapper_service import TapperService

class TestTapperService:

    def test_tap_sequence(self):
        # Use HTTP-only station to avoid MQTT fallback issues
        service = TapperService("http_only_station")

        service.connect()

        sequences.safe_tap_card2(service.protocol)
        time.sleep(2)
        sequences.safe_tap_card1(service.protocol)


