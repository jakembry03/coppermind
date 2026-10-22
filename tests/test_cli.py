from coppermind.cli import GREETING, main

def test_main_prints_greeting_and_succeeds(capsys):
    exit_code = main()
    captured = capsys.readouterr()

    assert captured.out.strip() == GREETING
    assert exit_code == 0
