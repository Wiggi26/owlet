"""Specific failure signatures for confirmed audit defects, not broad xfails."""


class StaleMeasurementDefect(AssertionError):
    """A years-old source timestamp is still presented as a live measurement."""


class InvalidOxygenDefect(AssertionError):
    """The known oxygen sentinel remains available as a valid percentage."""


class UnknownSleepDefect(AssertionError):
    """The known unknown sleep code is interpreted as awake."""


class PollingOptionDefect(AssertionError):
    """Saving options leaves the running coordinator at the old interval."""
