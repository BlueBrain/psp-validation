import psp_validation.cv_validation.utils as test_module


def test_ensure_file_exists(tmp_path):
    test_dir = tmp_path / "new_dir"
    assert not test_dir.exists()
    test_module.ensure_dir_exists(test_dir)
    assert test_dir.is_dir()
