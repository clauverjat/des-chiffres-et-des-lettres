#!/usr/bin/env python3

# Author: clauverj
# Author: sthoby

from z3 import *
from time import time

def push(v):
    def perform_action(_solver, etat):
        etat.push(v)
    return perform_action

def mul(solver, etat):
    a, b = (etat.get_top(), etat.get_top(1))
    # 2 POP() + 1 PUSH()
    etat.pop(1)
    etat.pop(1)
    etat.push(1)
    solver.add(etat.get_top() == a*b)

def add(solver, etat):
    a, b = (etat.get_top(), etat.get_top(1))
    # 2 POP() + 1 PUSH()
    etat.pop(1)
    etat.pop(1)
    etat.push(1)
    solver.add(etat.get_top() == a+b)

def sub(solver, etat):
    a, b = (etat.get_top(), etat.get_top(1))
    # 2 POP() + 1 PUSH()
    etat.pop(1)
    etat.pop(1)
    etat.push(1)
    solver.add(etat.get_top() == a-b)

def div(solver, etat):
    a, b = (etat.get_top(), etat.get_top(1))
    # 2 POP() + 1 PUSH()
    etat.pop(1)
    etat.pop(1)
    etat.push(1)
    # Prevent division by zero
    solver.add(Implies(b==0, False))
    solver.add(Implies(b!=0, etat.get_top() == a/b))

class Etat():
    def __init__(self, nb_tab=0, pos=0):
        self.arr = Array(f"pile_0", IntSort(), IntSort())
        self.pos = pos

    def push(self, v):
        self.pos += 1
        self.arr = Store(self.arr, self.pos-1, v)

    def pop(self, n):
        self.pos -= 1

    def get_(self):
        return self.arr

    def get_size(self):
        return self.pos

    def get_top(self, offset=0):
        return self.arr[self.pos-1-offset]

    def __getitem__(self, idx):
        if idx < 0 or idx >= self.pos:
            # Return an impossible predicate to prevent such state to occur
            return False
        return self.arr[idx]

class Predicat():
    def __init__(self, generator):
        self.generator = generator

    def check(self, solver, etat):
        if self.generator != None:
            solver.add(self.generator(etat))


class Success(Exception):
    def __init__(self, val):
        self.val = val

class Failure(Exception):
    pass


class Automate():
    POSSIBLE_ACTIONS=[mul, add, sub, div]
    def __init__(self, constantes, predicat_initial, predicat_final, max_depth):
        self.etat = Etat()
        self.constantes = constantes
        self.actions = []
        self.predicat_initial = predicat_initial
        self.predicat_final = predicat_final
        self.solver = Solver()
        self.max_depth = max_depth
        self.depth = 0

    def avance(self):
        self.depth += 1
        if self.depth == self.max_depth:
            return
        self.solver.push()
        for i in self.POSSIBLE_ACTIONS:
            i(self.solver, self.etat)
            self.solver.push()
            self.predicat_final.check(self.solver, self.etat)
            status = self.solver.check()
            if status == sat:
                raise Success(self.solver.model)
            else:
                # On essaie tous les fils
                self.avance()
                # Rien trouvé, on rollback
                self.solver.pop()
        for i in constantes:
            del constantes[i]
            push(i)(self.solver, self.etat)

            status = self.solver.check()
            if status == sat:
                raise Success(self.solver.model)
            else:
                self.avance()
                # Rien trouvé, on rollback
                # On remets la constante dans la liste, puisqu'elle n'est pas utilisée
                self.constantes.push(i)
                self.solver.pop()
        raise Failure()

    def run(self):
        self.predicat_initial.check(self.solver, self.etat)
        self.solver.push()
        try:
            self.avance()
        except Success as s:
            return s.val

res = Automate([1, 2, 2], Predicat(None), Predicat(lambda v: v[0] == 5), 15).run()
print(res)
