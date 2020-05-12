from z3 import *
from helpers import solve_and_print

ctx = Context(model=True, proof=True)
solver = Solver(ctx=ctx)

a, b, c, d, e= Ints("a b c d e", ctx=ctx)

print("creating a > b + 2: ")
solver.add(a > b + 2)
print("creating a = 2 * c + 10: ")
solver.add(a == 2*c + 10)
print("creating b + c <= 1000: ")
solver.add(b + c <= 1000)

print("creating d >= e")
solver.add(d >= e)
solve_and_print(solver)

print("Adding new constraint on a...")
solver.add(Not(a == 0))
solve_and_print(solver)