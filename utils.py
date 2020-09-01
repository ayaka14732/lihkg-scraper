import math

def gen_ranges(first, last, count):
    '''
    >>> list(gen_ranges(100, 300, 4))
    [(100, 150), (150, 200), (200, 250), (250, 300)]
    >>> list(gen_ranges(100, 300, 3))
    [(100, 167), (167, 234), (234, 300)]
    '''
    step = math.ceil((last - first) / count)
    while first < last:
        end = max(first + 1, min(first + step, last))
        yield first, end
        first = end
