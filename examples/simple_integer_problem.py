from z3 import *
from time import time

def solveAndPrint(solver):
    begin = time()
    status =  solver.check()
    if status == sat:
        print("Problem is SAT!")

        m = solver.model()
        print(m)
    elif status == unsat:
        print("UNSAT")
    elif status == unknown:
        print("UNKNOWN")
    else:
        raise ValueError
    end = time()
    print("Time to solve:", end-begin, "s")

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
solveAndPrint(solver)

print("Adding new constraint on a...")
solver.add(Not(a == 0))
solveAndPrint(solver)