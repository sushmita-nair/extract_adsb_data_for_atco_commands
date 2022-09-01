from datetime import timezone

from sectorization import get_sector_bounds, coordinates


class ControllerInput:
    def __init__(self, departure, command, callsign, sector_code, timestamp, time_str, sector, destination, cmd_index):
        self.departure = departure
        self.commands = [command]
        self.callsign = callsign
        self.sector_code = sector_code
        self.timestamp = timestamp
        self.time_str = time_str
        timestamp = self.timestamp.replace(tzinfo=timezone.utc).timestamp()
        # Hour boundary in seconds used for filtering in the query
        self.hour = int(timestamp - (timestamp % 3600))
        self.sector = sector
        self.destination = destination
        self.cmd_index = cmd_index
        self.sector_bounds = get_sector_bounds(self.sector, self.time_str, self.timestamp.strftime("%Y-%m-%d"))
        # Use self.bounds for querying open-sky. Can never be null.
        self.bounds = self.sector_bounds[:4] if self.sector_bounds else coordinates[self.sector_code]

