##################
##              ##
##    OTCBot    ##
## ------------ ##
##################


import os


def get_env(
        key: str
    ) -> str:

    value = os.environ.get(key)

    if value is None:
        raise KeyError(key)

    return value


def get_env_id(
        key: str
    ) -> int:

    value = get_env(key)

    if not value.isnumeric():
        raise ValueError(value)

    return int(value)
