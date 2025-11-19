from click.testing import CliRunner

from src.hiveden.cli import main



def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
