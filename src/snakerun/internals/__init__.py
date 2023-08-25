try:
    from .internals_rs import parse_pep_722
except ImportError:
    print("Falling back to python parser.")
    from .pep_722_parser import parse_pep_722
