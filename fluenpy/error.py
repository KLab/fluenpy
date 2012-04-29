
class ConfigError(Exception):
    pass

class ConfigParserError(ConfigError):
    pass

class BufferError(Exception):
    pass

class BufferChunkLimitError(BufferError):
    pass

class BufferQueueLimitError(BufferError):
    pass

