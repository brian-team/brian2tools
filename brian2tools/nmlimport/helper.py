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


# Generate proximal points for a segment if not present already
def adjust_morph_object(segments):
    for segment in segments:
        if segment.proximal is None:
            if segment.parent is not None:
                parent_seg = get_parent_segment(segment, segments)
                segment.proximal=parent_seg.distal
            else:
                raise ValueError("Segment {0} has no parent and no proximal "
                                 "point".format(segment))
    return segments


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


def perform_dfs(mapping, node, counter, children):
    mapping[node] = counter
    new_counter = counter + 1
    for child in children[node]:
        new_counter = perform_dfs(mapping, child, new_counter, children)
    return new_counter


# Return id mappings of segments present in .nml file
def get_id_mappings(segments, parent_node=None, counter=0):
    if parent_node is None:
        parent_node = get_root_segment(segments).id

    mapping = {}
    children = get_child_segments(segments)
    perform_dfs(mapping, parent_node, counter, children)
    return mapping


def get_segment_dict(segments):
    segdict={}
    for s in segments:
        segdict[s.id]=s
    return segdict


def get_segment_group(m, grp):
    for g in m.segment_groups:
        if g.id == grp:
            return g


def resolve_member(mem_list, members):
    if members is not None:
        for m in members:
            mem_list.append(m.segments)


def resolve_includes(l, grp, m):
    if grp.includes is not None:
        for g in grp.includes:
            resolve_includes(l, get_segment_group(m, g.segment_groups), m)
    resolve_member(l, grp.members)


def get_root_segment(segments):
    for x in segments:
        if x.parent is None:
            return x
