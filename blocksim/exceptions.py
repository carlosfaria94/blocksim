class InvalidTransaction(Exception):
    pass


class VerificationFailed(Exception):
    pass


class UnsignedTransaction(InvalidTransaction):
    pass
