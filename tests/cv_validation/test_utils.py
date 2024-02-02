import os
import importlib.resources
from tempfile import TemporaryDirectory

import psp_validation.cv_validation.utils as test_module
from psp_validation.cv_validation import templates


def test_ensure_file_exists():
    with TemporaryDirectory("test_utils") as folder:
        test_dir = os.path.join(folder, "new_dir")
        assert not os.path.exists(test_dir)
        test_module.ensure_dir_exists(test_dir)
        assert os.path.isdir(test_dir)
