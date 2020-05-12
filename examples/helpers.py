from time import time
from z3 import *

def solve_and_print(solver):
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