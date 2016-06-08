class DBTimeoutException(Exception):
    pass


class NonExistentDatabase(Exception):
    pass


class NonExistentTemplate(NonExistentDatabase):
    pass


class ImportInProgress(Exception):
    pass


class ImportDataError(Exception):
    pass


class NotReachableException(Exception):
    pass


class ContainerRunning(Exception):
    pass
