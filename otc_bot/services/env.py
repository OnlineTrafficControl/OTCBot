##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

# services.env #


import os
from dotenv import load_dotenv


load_dotenv()


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
