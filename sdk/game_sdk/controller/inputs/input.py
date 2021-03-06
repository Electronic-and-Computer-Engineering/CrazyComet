class Input:
    """
        Base class for all user inputs
    """

    def __init__(self, seat: int, name: str):
        """
            Abstract init method
            Arguments:
                seat: controller seat
                name: controller name
        """
        self._name = name

    async def init(self, seat: int):
        """
            Executed at the beginning of the game. Initialize all controller inputs

            Arguments:
                seat: controller seat
        """

    async def reset(self, seat: int):
        """
            Executed at the end of the game. Resets all controller inputs

            Arguments:
                seat: controller seat
        """

    async def close(self, seat: int):
        """
            Called when the program exits.

            Arguments:
                seat: controller seat
        """

    @property
    def name(self):
        """
            control name
        """
        return self._name
