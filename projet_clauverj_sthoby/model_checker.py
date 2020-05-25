from dataclasses import dataclass
from itertools import islice
from typing import Dict, List, Any, Optional
from uuid import uuid4
from logging import debug

from z3 import *


@dataclass
class Transition:
    formula: z3.BoolRef
    actions_done: Dict[str, z3.BoolRef]

    def string(self, model: z3.ModelRef):
        for name, action_done in self.actions_done.items():
            if model[action_done]:
                return name


def transition(state1, state2, action_formulas):
    # on créé des booléens pour indiquer si une action a été choisie
    actions_done = {action: Bool(str(uuid4())) for action in action_formulas}
    formula = And(
        # Si le booléen correspondant à l'action est vrai alors l'action doit être effectuée
        *[Implies(actions_done[action], action_formulas[action](state1, state2)) for action in
          action_formulas],
        # Une et une seule action parmi les différentes possibles doit être choisie
        AtLeast(*actions_done.values(), 1),
        AtMost(*actions_done.values(), 1),
    )
    return Transition(actions_done=actions_done, formula=formula)


@dataclass
class Solution:
    z3_model: z3.z3.ModelRef
    transitions: List[Transition]
    states: List[Any]
    difference: z3.z3.Int = 0

    def actions_effectuees(self):
        return (transition.string(self.z3_model) for transition in self.transitions)


def bmc(State, action_formulas, init_state_predicate, final_state_predicate, max_nb_transitions
        ) -> Optional[Solution]:
    """
    Bounded Model Checking
    :param State: Une classe décrivant un état du système
    :param action_formulas: Un dictionnaire qui au nom d'une action associe une fonction qui prend
    en argument un état de départ s_pre et un état d'arrivée s_post et retourne la formule T(s_pre, s_post)
    où T est le prédicat caractérisant la relation de transition du système
    :param init_state_predicate: Formule Z3 (prédicat) sur l'état initial du système
    :param final_state_predicate: Formule Z3 (prédicat) sur l'état final du système
    :param max_nb_transitions: Borne maximale du nombre de transitions effectué
    :return: Un objet de la classe Model ou None si le problème est insatisfiable
    """

    states = []
    transitions = []

    solver = Solver()

    states.append(State(0))
    solver.add(init_state_predicate(states[0]))

    for i in range(max_nb_transitions):
        debug(f"Step {i}/{max_nb_transitions}")
        states.append(State(i + 1))
        trans = transition(states[i], states[i + 1], action_formulas)
        transitions.append(trans)
        solver.add(trans.formula)
        # sauvegarde de l'état
        solver.push()
        # vérification de la propriété sur l'état final
        solver.add(final_state_predicate(states[i + 1]))
        status = solver.check()
        if status == sat:
            return Solution(
                z3_model=solver.model(),
                transitions=transitions,
                states=states
            )
        elif status == unknown:
            raise AssertionError("Z3 formula satisfiability could not be determined")
        elif status == unsat:
            pass
        else:
            raise AssertionError("Cas non prévu")
        # on remet le solver à l'état d'avant
        solver.pop()
    else:
        # Problème non satisfiable
        return None


def _bounded_models(State, action_formulas, init_state_predicate):
    """
    Génère des états et des formules sans l'état final pour faciliter
    l'écriture de bmc_approx.
    :param State:
    :param action_formulas:
    :param init_state_predicate:
    :return: Generator[formulas, states, transitions]
    """
    states = [State(0)]
    transitions = []
    formulas = [init_state_predicate(states[0])]
    i = 0
    while True:
        states = states + [State(i + 1)]
        trans = transition(states[i], states[i + 1], action_formulas)
        transitions = transitions + [trans]
        formulas = formulas + [trans.formula]
        yield formulas, states, transitions
        i += 1


def bmc_approx(State, action_formulas, init_state_predicate, final_state_approx_constraints,
               max_nb_transitions) -> Optional[Solution]:
    """
    Bounded Model Checking avec approximation
    :param State: Une classe décrivant un état du système
    :param action_formulas: Un dictionnaire qui au nom d'une action associe une fonction qui prend
    en argument un état de départ s_pre et un état d'arrivée s_post et retourne la formule T(s_pre, s_post)
    où T est le prédicat caractérisant la relation de transition du système
    :param init_state_predicate: Fonction prenant un état et renvoyant un prédicat (formule Z3) décrivant l'état initial du système
    :param final_state_predicate: Fonction prenant un état et renvoyant un dictionnaire avec deux clés
        * 'hard' un prédicat (formule Z3) décrivant les contraintes qui doivent être impérativement
        respectées pour que l'état final soit acceptable
        * 'criterion', un critère à minimiser (un entier ou un bitvector) sur l'état final
    :param max_nb_transitions: Borne maximale du nombre de transitions effectués
    :return: Un objet de la classe Model ou None si le problème est insatisfiable
    """
    best_model = None
    for i, (formula, states, transitions) in enumerate(
            islice(_bounded_models(State, action_formulas, init_state_predicate),
                   max_nb_transitions)):
        debug(f"Step {i + 1}/{max_nb_transitions}")
        solver = Optimize()
        solver.add(formula)
        final_state_constraints = final_state_approx_constraints(states[i + 1])
        solver.add(final_state_constraints['hard'])
        v = solver.minimize(final_state_constraints['criterion'])
        status = solver.check()
        if status == sat:
            cur_score = v.value().as_long()
            if best_model == None or best_model.difference > cur_score:
                best_model = Solution(
                    z3_model=solver.model(),
                    transitions=transitions,
                    states=states,
                    difference=cur_score,
                )
                debug(f"SAT score : {cur_score}")
            if cur_score == 0:
                break
        elif status == unknown:
            raise AssertionError("Z3 formula satisfiability could not be determined")
        elif status == unsat:
            debug("UNSAT")
            pass
        else:
            raise AssertionError("Cas non prévu")
    return best_model
