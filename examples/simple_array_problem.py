from z3 import *
from helpers import solve_and_print

ctx = Context(model=True, proof=True)
solver = Solver(ctx=ctx)

my_array_v = Array("my_array_v", IntSort(ctx), BitVecSort(8,ctx=ctx))

solver.add(
    my_array_v[0] == BitVecVal(1,8, ctx=ctx)
)


solver.add(
    my_array_v[1] == BitVecVal(2,8, ctx=ctx)
)

solve_and_print(solver)


my_array_v_up1 = Array("my_array_v_up1", IntSort(ctx), BitVecSort(8, ctx))
solver.add(my_array_v_up1 == Store(my_array_v, 1, 5))
my_array_v_up2 = Array("my_array_v_up2", IntSort(ctx), BitVecSort(8, ctx))
solver.add(my_array_v_up2 == Store(my_array_v_up1, 2, 42))

solve_and_print(solver)
tab = [BitVec(f"my_array_v[{i}]",8, ctx=ctx) for i in range(4)]
solver.add([my_array_v[i] == var for i,var in enumerate(tab)])
solve_and_print(solver)