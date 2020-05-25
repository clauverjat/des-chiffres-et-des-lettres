from chiffres import solve, solution_resulting_number
from games import *

def test_solve_exact():
    assert None != solve(game1_1, approx=False, bits=8, no_overflow=False)

def test_solve_exact2():
    assert None == solve(game1_2, approx=False, bits=8, no_overflow=False)

def test_solve_exact3():
    # Trouve le résultat en s'appyant sur les overflows...
    assert None != solve(game1_1, approx=False, bits=14, no_overflow=False)

def test_solve_exact4():
    assert None == solve(game1_2, approx=False, bits=14, no_overflow=False)

def test_solve_exact5():
    assert None != solve(game2, approx= False, bits=14, no_overflow=True)
    assert None != solve(game3_1, approx=False, bits=10, no_overflow=True)
    assert None != solve(game3_2, approx=False, bits=10, no_overflow=True)
    assert None != solve(game4, approx=False, bits=10, no_overflow=True)

def test_solve_approx():
    m = solve(game1_2, approx=True, bits=14, no_overflow=True)
    assert solution_resulting_number(m) == 120
    m = solve(game2, approx=True, bits=14, no_overflow=True)
    assert solution_resulting_number(m) == game2.objective

