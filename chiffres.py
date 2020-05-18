import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
from dataclasses import dataclass
from typing import Any, List
import pytest
from model_checker import bmc, bmc_approx
from uuid import uuid1

from z3 import *
from examples.helpers import *
from functools import partial


game_example = {"numbers": [8, 10, 2, 1, 5, 50], "objective": 899}

def mk_State(numbers):
    @dataclass
    class State:
        index: z3.Int
        stack: z3.Array
        numbers_used: List[z3.Bool]

        def __init__(self, i):
            self.index=Int(f"index[{i}]")
            self.stack=Array(f"stack[{i}]", IntSort(), IntSort())
            self.numbers_used=[Bool(f"used[{i}]({n})") for n, _ in enumerate(numbers)]

        def string(self, model):
            stack_repr = ", ".join((
                str(model.eval(self.stack[i]).as_long()) for i in range(model[self.index].as_long())
            ))
            numbers_used = " ".join((
                f"🗹 {number_used}"
                if model[self.numbers_used[i]]
                else f"☐ {number_used}"
                for i, number_used in enumerate(numbers)
            ))
            return f"Stack : [{stack_repr}]" + "\n" + f"Numbers : {numbers_used}"
    return State


def init_predicate(state):
    return And(
        state.index == 0,
        And([Not(number_used) for number_used in state.numbers_used]),
    )


def add(state_pre, state_post):
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,  # post
        state_post.stack == Store(
            state_pre.stack,
            state_pre.index - 2,
            state_pre.stack[state_pre.index - 1] + state_pre.stack[state_pre.index - 2],
        ),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def sub(state_pre, state_post):
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,
        state_post.stack == Store(
            state_pre.stack,
            state_pre.index - 2,
            state_pre.stack[state_pre.index - 1] - state_pre.stack[state_pre.index - 2],
        ),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def mult(state_pre, state_post):
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,  # post
        state_post.stack == Store(
            state_pre.stack,
            state_pre.index - 2,
            state_pre.stack[state_pre.index - 1] * state_pre.stack[state_pre.index - 2],
        ),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def div(state_pre, state_post):
    quotient = Int(str(uuid1()))
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,
        state_pre.stack[state_pre.index - 2] != 0,
        state_pre.stack[state_pre.index - 1] - quotient * state_pre.stack[state_pre.index - 2] == 0,
        state_post.stack == Store(state_pre.stack, state_pre.index - 2, quotient),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def push(numbers, ith, state_pre, state_post):
    return And(
        # précondition
        # la constante n'a pas déjà était utilisé
        Not(state_pre.numbers_used[ith]),
        # état de la pile après l'opération
        state_post.numbers_used[ith],
        *[used_pre == used_post
          for i, (used_pre, used_post) in enumerate(
                zip(state_pre.numbers_used, state_post.numbers_used)
            )
          if i != ith],
        state_post.index == state_pre.index + 1,
        state_post.stack == Store(state_pre.stack, state_pre.index, numbers[ith]),
    )



def final_predicate(target_number, state):
    return And(state.index == 1, state.stack[0] == target_number)


def solve_exact(input):
    actions = {
        **{"add": add, "sub": sub, "mult": mult, "div": div},
        **{f"push_{i}": partial(push, input["numbers"], i) for i in range(len(input["numbers"]))},
    }
    # Question 1 - Diamètre de réoccurence du système :
    # * Chaque constante peut être poussée au plus une fois donc le nombre de push est inférieur ou
    # égal au Nombre de constantes

    # * Les autres opérations (+, -, +, /) diminuent à chaque fois d'une unité la taille de la pile
    # * La taille maximale de la plus est égal aux nombres de constantes (car la seule opération qui
    #    augmente la taille de la pile est push)
    # * Donc il y au plus Nombre de constantes  - 1 autres opérations.
    # Au total le diamètre de réoccurence est inférieur ou égal à 2 * Nombre de constantes - 1
    #
    # Réciproquement dans le cas général on ne peut pas faire mieux
    # En effet considérons les (P_n) problème des chiffres définis par
    #     * C = [1,1,1,1 (n fois)]
    #     * Objectif = n
    # Alors la seule solution est de faire le calcul 1 + 1 + 1 + ... + 1 (n fois) (à l'associativité près)
    # Ce calcul nécessite n push, et n - 1 opérations Addition d'où 2*n - 1.
    # Ainsi dans le cas général le diamètre de réoccurence est égal 2 * Nombre de constantes - 1

    diametre_reoccurence = 2 * len(input["numbers"]) - 1

    return bmc(mk_State(input['numbers']), actions, init_predicate, partial(final_predicate, input["objective"]) , diametre_reoccurence)


def solve_approx(input):
    actions = {
        **{"add": add, "sub": sub, "mult": mult, "div": div},
        **{f"push_{i}": partial(push, input["numbers"], i) for i in
           range(len(input["numbers"]))},
    }

    diametre_reoccurence = 2 * len(input["numbers"]) - 1

    return bmc_approx(mk_State(input['numbers']), actions, init_predicate,
               partial(final_state_approx_constraints, input["objective"]), diametre_reoccurence)


def abs(x):
    return If(x >= 0,x,-x)


def final_state_approx_constraints(target_number, state):
    distance = Int(str(uuid1()))
    return {
        'hard': And(state.index == 1,distance == abs(state.stack[0] - target_number), distance >= 0),
        'criterion': distance
    }




def show_result(model):
    print("Résultat ", model.z3_model.eval(model.states[-1].stack[0]))
    print("Actions : ", *(transition.string(model.z3_model) for transition in model.transitions))
    for i, state in enumerate(model.states):
        print("―" * 50)
        print("State", i)
        print(state.string(model.z3_model))

if __name__ == '__main__':
    #model = solve_exact(game_example)
    #show_result(model)
    game_example={"numbers":[10, 20, 30, 40], "objective": 119}
    print("Objectif", game_example['objective'])
    model = solve_approx(game_example)
    show_result(model)


