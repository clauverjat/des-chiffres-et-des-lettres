from z3 import *
from helpers import solve_and_print

ctx = Context(model=True, proof=True)
solver = Solver(ctx=ctx)

a, b, c = BitVecs("a b c",4, ctx=ctx)



solver.add(a > b + BitVecVal(2, 4, ctx=ctx))
solver.add(a == 2 * c + 10)
solver.add(b + c <= 10)

solve_and_print(solver)