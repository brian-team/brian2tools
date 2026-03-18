import pytest
from brian2tools.nmlimport.nml import validate_morphology, ValidationException


class MockParent:
    fraction_along = 1


class MockSegment:
    def __init__(self, seg_id, parent=None, name='seg'):
        self.id = seg_id
        self.parent = parent
        self.name = name


def test_validate_morphology_passes_single_root():
    """Valid morphology: one root, one child should not raise."""
    root = MockSegment(seg_id=0, parent=None, name='soma')
    child = MockSegment(seg_id=1, parent=MockParent(), name='dend')
    validate_morphology([root, child])  # must not raise


def test_validate_morphology_raises_two_roots():
    """Two segments with no parent should raise ValidationException."""
    seg1 = MockSegment(seg_id=0, parent=None, name='soma')
    seg2 = MockSegment(seg_id=1, parent=None, name='axon')
    with pytest.raises(ValidationException):
        validate_morphology([seg1, seg2])


def test_validate_morphology_raises_bad_fraction_along():
    """fraction_along not in [0, 1] should raise NotImplementedError."""
    class BadParent:
        fraction_along = 0.5

    root = MockSegment(seg_id=0, parent=None, name='soma')
    child = MockSegment(seg_id=1, parent=BadParent(), name='dend')
    with pytest.raises(NotImplementedError):
        validate_morphology([root, child])