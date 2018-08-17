from pprint import pformat
from collections import defaultdict


# Returns parent segment
def get_parent_segment(segment, segments):
    for s in segments:
        if s.id == segment.parent.segments:
            return s


# Pretty format data
def formatter(datum):
    a = pformat(datum)
    if len(a) > 160:
        a = a[0:160] + "[...]"
    return a


# Returns a dictionary of child segments of each segment, segment id is a key.
def get_child_segments(segments):
    children = defaultdict(list)
    root = None
    for segment in segments:
        if segment.parent is None:
            root = segment.id
        else:
            children[segment.parent.segments].append(segment.id)

    assert root is not None
    return children
