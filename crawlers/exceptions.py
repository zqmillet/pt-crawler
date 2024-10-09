class CannotGetUserInformationException(Exception):
    def __init__(self) -> None:
        super().__init__('cannot get user information')
