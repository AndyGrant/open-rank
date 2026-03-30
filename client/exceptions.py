
class OpenRankHardwareReqError(Exception):
    pass

class OpenRankGeneralRequestError(Exception):
    pass

class OpenRankFailedDockerLoadError(Exception):
    pass

class OpenRankAuthenticationError(Exception):
    pass

class OpenRankMismatchedFastchessError(Exception):
    pass

class OpenRankCorruptedTarballError(Exception):
    pass

class OpenRankCorruptedBookError(Exception):
    pass

class OpenRankBenchingFailed(Exception):
    pass
