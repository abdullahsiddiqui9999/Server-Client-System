class ClientOfflineException( Exception ):
    pass

class ClientIsBusyException( Exception ):
    pass

class ClientUnreachableException( Exception ):
    pass


class UnknownCallerException( Exception ):
    pass


class UserValidationFailedException( Exception ):
    pass


class TerminateReceivingThreadException( Exception ):
    pass