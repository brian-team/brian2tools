from pprint import pformat

# Return segment type depending on proximal and distal diameter
def get_segment_type(segment):
    if segment.proximal.diameter==segment.distal.diameter:
        return "cylinder"
    return "section"


# Get parent segment
def get_parent_segment(segment,segments):
    for s in segments:
        if s.id==segment.parent.segments:
            return s


# Check if distal of first segment joins with proximal of next segment
def are_segments_joined(segment1,segment2):
    if segment2.parent==None:
        if segment1.proximal.x==segment2.proximal.x \
                and segment1.proximal.y==segment2.proximal.y \
                and segment1.proximal.z==segment2.proximal.z:
            return True
    return segment1.proximal.x==segment2.distal.x \
           and segment1.proximal.y==segment2.distal.y \
           and segment1.proximal.z==segment2.distal.z


# Shift coordinates for further processing
def shiftCoords(x):
    if x:
        if x[0]:
            x[:]= [a - x[0] for a in x]
        else:
             x[:]= [a + x[0] for a in x]
    return x


# Pretty format data
def formatter(datum):
    a = pformat(datum)
    if len(a) > 160:
        a = a[0:160] + "[...]"
    return a
