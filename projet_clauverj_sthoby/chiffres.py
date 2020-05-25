import logging
import sys

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
from dataclasses import dataclass
from typing import List, Optional
from model_checker import bmc, bmc_approx, Solution
from uuid import uuid4
from z3 import *
from time import time
from functools import partial



@dataclass
class GameInput:
    """
    Description du problème
    :example: GameInput(numbers= [8, 10, 2, 1, 5, 50], objective=899)
    """
    numbers: List[int]
    objective: int

def mk_State(numbers: List[int], bits: int):
    """
    Retourne une classe State qui représente un état du modèle à vérifier
    :param numbers: la liste des constantes entières c_1, ..., c_N
    :param bits: le nombre de bits des bits vecteurs utilisés
    :return: Une classe qui modèle un état
    """
    @dataclass
    class State:
        """
        L'état de l’automate est représenté par :
        * un tableau de bitvecteurs encodant la pile.
        Attention : on représente les entiers de façon non signé.
        * l’index de la prochaine cellule libre du tableau
        * une liste de booléens qui indique si la ième constante a déjà été utilisée
        """
        index: z3.ArithRef
        stack: z3.ArrayRef
        numbers_used: List[z3.BoolRef]

        def __init__(self, i):
            self.index = Int(f"index[{i}]")
            self.stack = Array(f"stack[{i}]", IntSort(), BitVecSort(bits))
            self.numbers_used = [Bool(f"used[{i}]({n})") for n, _ in enumerate(numbers)]

        def string(self, model: Model) -> str:
            """
            Chaine de caractères représentant l'état self avec les
            valeurs attribuées au model après résolution
            """
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
    """
    Retourne un prédicat (formule Z3) caractérisant les états initiaux du système
    """
    return And(
        state.index == 0,
        And([Not(number_used) for number_used in state.numbers_used]),
    )


def add_formula(no_overflow: bool, state_pre, state_post):
    """
    Prédicat vrai si state_pre et state_post sont des états liés par l'action add
    :param no_overflow: vrai si on interdit les overflow faux sinon
    :param state_pre: state avant l'action
    :param state_post: state après l'action
    :return: prédicat (formule z3)
    """
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,  # post
        BVAddNoOverflow(state_pre.stack[state_pre.index - 1] , state_pre.stack[state_pre.index - 2], signed=False) if no_overflow else True,
        state_post.stack == Store(
            state_pre.stack,
            state_pre.index - 2,
            state_pre.stack[state_pre.index - 1] + state_pre.stack[state_pre.index - 2],
        ),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def sub_formula(state_pre, state_post):
    """
    Prédicat vrai si state_pre et state_post sont des états liés par l'action sub
    :param state_pre: state avant l'action
    :param state_post: state après l'action
    :return: prédicat (formule z3)
    """
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,
        # attention ne pas utiliser la comparaison >= car elle suppose des représentations signées,
        # or nous avons choisi une représentation non signée des entiers.
        UGE(state_pre.stack[state_pre.index - 1],state_pre.stack[state_pre.index - 2]),
        state_post.stack == Store(
            state_pre.stack,
            state_pre.index - 2,
            state_pre.stack[state_pre.index - 1] - state_pre.stack[state_pre.index - 2],
        ),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def mult_formula(no_overflow: bool, state_pre, state_post):
    """
    Prédicat vrai si state_pre et state_post sont des états liés par l'action mult
    :param no_overflow: vrai si on interdit les overflow faux sinon
    :param state_pre: state avant l'action
    :param state_post: state après l'action
    :return: prédicat (formule z3)
    """
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,  # post
        BVMulNoOverflow(state_pre.stack[state_pre.index - 1], state_pre.stack[state_pre.index - 2],
                         signed=False) if no_overflow else True,
        state_post.stack == Store(
            state_pre.stack,
            state_pre.index - 2,
            state_pre.stack[state_pre.index - 1] * state_pre.stack[state_pre.index - 2],
        ),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def div_formula(state_pre, state_post):
    """
    Prédicat vrai si state_pre et state_post sont des états liés par l'action div
    :param state_pre: state avant l'action
    :param state_post: state après l'action
    :return: prédicat (formule z3)
    """
    quotient = BitVec(str(uuid4()), state_pre.stack[0].size())
    return And(
        # précondition
        # deux éléments au moins dans la pile
        state_pre.index >= 2,
        # état de la pile après l'opération
        state_post.index == state_pre.index - 1,
        state_pre.stack[state_pre.index - 2] != 0,
        # Bien que la division de non signés ne puisse pas produire d'overflow
        # On doit quand même empêcher l'overflow de la multiplication
        # sans quoi on pourrait obtenir d'étrange résultat pour la division euclidienne
        # en effet modulo 2^n on perd l'unicité du quotient de la division euclidienne
        # par exemple sur 2 bits on a 2 = 1*2  mais aussi 2 = 3 * 2
        BVMulNoOverflow(quotient, state_pre.stack[state_pre.index - 2], signed=False),
        quotient * state_pre.stack[state_pre.index - 2] == state_pre.stack[state_pre.index - 1],
        state_post.stack == Store(state_pre.stack, state_pre.index - 2, quotient),
        And([used1 == used2 for used1, used2 in
             zip(state_pre.numbers_used, state_post.numbers_used)]),
    )


def push_formula(numbers: List[int], ith: int, state_pre, state_post):
    """
    Prédicat vrai si state_pre et state_post sont des états liés par l'action push_{numbers[ith]}
    :param numbers: liste des constantes
    :param ith: indice de la constante à pousser (commence à 0)
    :param state_pre: état avant l'action
    :param state_post: état après l'action
    :return: prédicat (formule z3)
    """

    return And(
        # précondition
        # la constante n'a pas déjà était utilisée
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


def final_predicate(target_number: int, state):
    """
    Retourne un prédicat (formule Z3) caractérisant les états finaux du système
    :param target_number: le résultat recherché (l'objectif)
    ;param: state: un état du système
    """
    return And(state.index == 1, state.stack[0] == target_number)


def solve(input: GameInput, approx: bool, no_overflow: bool, bits: int) -> Optional[Solution]:
    """
    Résout le problème du "compte est bon"
    :param input:
    :param approx: True si on recherche la séquence d’actions qui produit le résultat
    le plus proche en valeur absolue du résultat demandé, False si on cherche une solution exacte.
    :param no_overflow: True si on interdit les dépassements d'entiers, False sinon
    :param bits: Nombre de bits des bit vecteurs
    :return:
    """
    for number in input.numbers:
        if number.bit_length() > bits:
            raise ValueError(f"{number} n'est pas représentable sur {bits} bits")
    if input.objective.bit_length() > bits:
        raise ValueError(f"L'objectif à atteindre {input.objective} n'est pas représentable sur {bits} bits")

    actions = {
        **{"add": partial(add_formula, no_overflow),
           "sub": sub_formula,
           "mult": partial(mult_formula, no_overflow),
           "div": div_formula},
        **{f"push_{i}": partial(push_formula, input.numbers, i) for i in range(len(input.numbers))},
    }

    diametre_reoccurence = 2 * len(input.numbers) - 1
    if approx:
        return bmc_approx(mk_State(input.numbers, bits), actions, init_predicate,
                          partial(final_state_approx_constraints, input.objective),
                          diametre_reoccurence)
    else:
        return bmc(mk_State(input.numbers, bits), actions, init_predicate,
               partial(final_predicate, input.objective), diametre_reoccurence)


def Abs(x: z3.z3.ExprRef) -> z3.z3.ExprRef:
    """
    Retourne une expression Z3 pour la valeur absolue d'un entier (ou bitvecteurs)
    """
    return If(x >= 0, x, -x)


def final_state_approx_constraints(target_number, state):
    """
    Prend un état et renvoie un dictionnaire avec deux clés
        * 'hard' un prédicat (formule Z3) décrivant les contraintes qui doivent être impérativement
        respectées pour que l'état final soit acceptable
        * 'criterion', un critère à minimiser (un entier ou un bitvector) sur l'état final
    :param target_number: le nombre recherché
    :param state: un état
    :return:
    """
    distance = BitVec(str(uuid4()), state.stack[0].size())
    return {
        'hard': And(state.index == 1, distance == Abs(state.stack[0] - target_number),
                    distance >= 0),
        'criterion': distance
    }

def solution_resulting_number(solution) -> int:
    # Le résultat du calcul est le premier nombre (et seul nombre) sur la pile
    # du dernier état
    return solution.z3_model.eval(solution.states[-1].stack[0])

def print_result(solution):
    if solution == None:
        print("Pas de solution")
    else:
        print("Résultat ", solution_resulting_number(solution))
        print("Actions : ", *solution.actions_effectuees())

        for i, state in enumerate(solution.states):
            print("―" * 50)
            print("State", i)
            print(state.string(solution.z3_model))


if __name__ == '__main__':
    begin = time()
    # Description d'un jeu sous la forme d'un dictionnaire
    # game_example = GameInput(numbers= [8, 10, 2, 1, 5, 50], objective=899)
    game_example = GameInput(numbers= [10, 20, 30, 40], objective=119)
    print("Objectif", game_example.objective)
    # Résolution exact (approx = False) ou approchée (approx = True)
    solution = solve(game_example, approx=True, no_overflow=True, bits=7)
    # model = solve(game_example, approx=True no_overflow=True, bits=7)

    # Affichage du résultat
    print_result(solution)
    end = time()
    print("Time to solve : ", end-begin, "s")
