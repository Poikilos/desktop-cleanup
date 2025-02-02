
def emit_cast(value):
    return "{}({})".format(type(value).__name__, repr(value))