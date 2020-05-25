# Auteurs
* clauverj (Corentin Lauverjat)
* sthoby (Simon Thoby)

## Préambule
Le code est divisé en plusieurs fichiers : 
* `games.py` contient des exemples d'entrée pour le jeu du *compte est bon* ;
* `chiffres.py` contient le code correspondant à la modélisation de l'état et des 
actions du jeu du *compte est bon* et l'affichage des résultats de la résolution ;
* `model_checker.py` contient le code des bounded model checkers, le but a été
de les rendre les plus génériques possible ;
* `test_chiffres.py` contient les tests (de type pytest) 

Le point d'entrée du code se trouve dans le fichier `chiffres.py` en dessous de `if __name__ == '__main__'` 

# Réponses aux questions
## Question 1 

**Diamètre de réoccurence du système**

Posons V = 2*(Nombre de constantes non utilisées) + Taille de la pile

(V comme variant)

Soit t une transition
* si t est un push, alors une constante est utilisée et la taille de la pile est incrémentée donc V est décrémenté
* si t est une opération arithmétique (+, -, \*, /) alors la taille de la pile est décrémentée et le nombre de constantes utilisées reste inchangé. Donc V est décrémenté également.
Donc à chaque transition V décroit strictement.
A l'état initial V = 2*(Nombre constantes non utilisées)
A l'état final   V >= 1 (la taille de la pile doit valoir 1)
Donc il y a au plus 2*(Nombre constantes non utilisées) - 1 transitions
Ainsi **le diamètre de réoccurence est inférieur ou égal à 2 * (Nombre de constantes) - 1**

Réciproquement **dans le cas général on ne peut pas faire mieux**.

En effet considérons les (P_n) problèmes des chiffres définis par
* C = [1,1, ... ,1 (n fois)]
* Objectif = n

Alors la seule solution est de faire le calcul 1 + 1 + ... + 1 (n fois) (à l'associativité près). Et ce calcul nécessite n push, et (n - 1) opérations "add" d'où 2*n - 1 transitions.

## Question 2
Voir la fonction push_formula de `chiffres.py` 
## Question 3 et 4 
Voir les fonctions add_formula, sub_formula, mult_formula, div_formula de `chiffres.py`
## Question 5
Voir la fonction transition de `model_checker.py`
## Question 6 
Voir la fonction init_predicate de `chiffres.py`
## Question 7 
Voir la fonction final_predicate de `chiffres.py`
## Question 8 
Voir la fonction `solve` de `chiffres.py`
Cette fonction s'occupe à la fois de la résolution exacte et approchée. Le choix se fait avec le paramètre booléen approx.
Pour la résolution exacte elle s'appuie sur la fonction
`bmc` de `model_checker.py`.
## Question 9
a. et b. voir final_state_approx_constraints de `chiffres.py` 
on regroupe les deux méthodes en une seule fonction qui donne à la fois
les contraintes à respecter impérieusement (hard), et le critère à minismiser (le crtière de qualité de l'approximation).

Pour solveApprox voir la fonction solve de `chiffres.py` avec le paramètre `approx=True`.

## Question 10 

On a rajouté des paramètres no_overflow sur les fonctions modélisant les actions concernées (add, mult) par le phénomène d'overflow.

## Exemple d'utilisation 
Code dans `chiffres.py`
```python
if __name__ == '__main__':
    begin = time()
    # Description d'un jeu sous la forme d'un dictionnaire
    game_example = GameInput(numbers= [10, 20, 30, 40], objective=119)
    print("Objectif", game_example.objective)
    # Résolution exact (approx = False) ou approchée (approx = True)
    solution = solve(game_example, approx=True, no_overflow=True, bits=7)

    # Affichage du résultat
    print_result(solution)
    end = time()
    print("Time to solve : ", end-begin, "s")

``` 

On exécute le script en entrant `python3 chiffres.py` dans une console et on obtient : 

```
Objectif 119
Résultat  120
Actions :  push_2 push_0 push_3 div mult
――――――――――――――――――――――――――――――――――――――――――――――――――
State 0
Stack : []
Numbers : ☐ 10 ☐ 20 ☐ 30 ☐ 40
――――――――――――――――――――――――――――――――――――――――――――――――――
State 1
Stack : [30]
Numbers : ☐ 10 ☐ 20 🗹 30 ☐ 40
――――――――――――――――――――――――――――――――――――――――――――――――――
State 2
Stack : [30, 10]
Numbers : 🗹 10 ☐ 20 🗹 30 ☐ 40
――――――――――――――――――――――――――――――――――――――――――――――――――
State 3
Stack : [30, 10, 40]
Numbers : 🗹 10 ☐ 20 🗹 30 🗹 40
――――――――――――――――――――――――――――――――――――――――――――――――――
State 4
Stack : [30, 4]
Numbers : 🗹 10 ☐ 20 🗹 30 🗹 40
――――――――――――――――――――――――――――――――――――――――――――――――――
State 5
Stack : [120]
Numbers : 🗹 10 ☐ 20 🗹 30 🗹 40
Time to solve :  2.276078939437866 s
```