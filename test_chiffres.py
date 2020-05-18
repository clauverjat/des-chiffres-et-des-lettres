from chiffres import solve_exact, show_result
from games import *


def test_solve_exact():
    assert None != solve_exact(game1_1)

def test_solve_exact2():
    assert None == solve_exact(game1_2)