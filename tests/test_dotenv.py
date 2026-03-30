from pathlib import Path


def test_pyproject_configures_pytest_to_load_repo_root_dotenv():
    assert 'env_files = [".env"]' in Path("pyproject.toml").read_text()
