from pprint import pformat
from collections import defaultdict
from brian2.spatialneuron.morphology import Section,Soma,Cylinder
from brian2.units import *

# Return segment type depending on proximal and distal diameter
def get_segment_type(segment):
    if segment.proximal.diameter == segment.distal.diameter:
        return "cylinder"
    return "section"


# Get parent segment
def get_parent_segment(segment, segments):
    for s in segments:
        if s.id == segment.parent.segments:
            return s


# Checks if distal of first segment connects with proximal of second segment
def are_segments_joined(segment1, segment2):
    return segment1.proximal.x == segment2.distal.x \
        and segment1.proximal.y == segment2.distal.y \
        and segment1.proximal.z == segment2.distal.z


# Shift coordinates for further processing
def shift_coords(x):
    if x:
        if x[0]:
            x[:] = [a - x[0] for a in x]
        else:
            x[:] = [a + x[0] for a in x]
    return x


# Pretty format data
def formatter(datum):
    a = pformat(datum)
    if len(a) > 160:
        a = a[0:160] + "[...]"
    return a


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

