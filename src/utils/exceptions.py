_ERR_PREFIX = 'ProactiveDS Error'

def raise_error(err_cls, msg: str):
    raise err_cls(f"{_ERR_PREFIX}: {msg}")


__all__ = [
    "raise_error"
]