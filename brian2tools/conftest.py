import pytest
from brian2.devices import reinit_and_delete


# Clean up after tests
@pytest.fixture(autouse=True)
def clean_up():
    yield    
    # clean up after the test (delete directory for standalone)
    reinit_and_delete()
