import time


class APIThrottle:
    """
    A class to manage API request intervals and track the average time between calls.

    This class keeps track of the time since the last API request, the total time elapsed between calls,
    and the number of calls made, to calculate the average time between API requests.

    Attributes:
        request_interval_ms (int): The minimum interval between API requests in milliseconds.
        last_request_time_ns (int): The timestamp of the last API request in nanoseconds.
        total_entry_interval_ms (int): The total time accumulated between calls in milliseconds.
        call_count (int): The number of calls made.
    """

    def __init__(self, request_interval_ms: int):
        """
        Initializes the APIThrottle with a specified request interval.

        Args:
            request_interval_ms (int): The minimum interval between API requests in milliseconds.
        """
        self.request_interval_ms = request_interval_ms
        self.last_request_time_ns = time.time_ns()
        self.previous_entry_time_ns = self.last_request_time_ns
        self.total_entry_interval_ms = 0
        self.call_count = 0

    def wait_for_next_request(self) -> None:
        """
        Waits for the time required to respect the request interval since the last request
        and updates the time tracking attributes.

        This method calculates the elapsed time since the last request, updates the total time
        tracking, increments the call count, and if necessary, sleeps for the remaining time
        until the next request can be made.
        """
        current_entry_time_ns = time.time_ns()
        if self.call_count > 0:  # Skip for the first call
            interval_since_last_entry_ms = (current_entry_time_ns - self.previous_entry_time_ns) // 1_000_000
            self.total_entry_interval_ms += interval_since_last_entry_ms

        self.call_count += 1
        wait_time_ns = (self.request_interval_ms * 1_000_000) - (current_entry_time_ns - self.last_request_time_ns)
        if wait_time_ns > 0:
            time.sleep(wait_time_ns / 1_000_000_000)  # Convert ns to seconds

        self.last_request_time_ns = time.time_ns()  # Update last request time
        self.previous_entry_time_ns = current_entry_time_ns  # Update the entry time for the next call

    def report(self) -> float:
        """
        Calculates and returns the average time between calls.

        Returns:
            The average time between calls in milliseconds, or None if no calls have been made.
        """
        if self.call_count <= 1:  # Need at least two calls to measure interval
            return -1
        return self.total_entry_interval_ms / (self.call_count - 1)