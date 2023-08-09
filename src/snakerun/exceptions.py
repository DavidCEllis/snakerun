class UnsupportedPlatform(Exception):
    """
    Operating system not supported - This is not actually an OS error
    """


class MetadataError(Exception):
    """
    Error for incorrect use of the metadata format
    """


class PyenvMissingError(FileNotFoundError):
    """
    Error for when pyenv is not installed
    """