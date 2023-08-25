try:
    from ._internals_rs import parse_pep722
except ImportError:
    print("Falling back to python internals.")
    from .pep722_parser import parse_pep722
