def floor_log2(v):
    """return floor(log2(v))."""
    assert isinstance(v, int)
    assert v > 0
    return v.bit_length() - 1


def ceil_log2(v):
    """return ceil(log2(v))."""
    assert isinstance(v, int)
    assert v > 0
    return (v - 1).bit_length()
