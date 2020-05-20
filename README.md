# Auteurs
Corentin Lauverjat, Simon Thoby

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

Alors la seule solution est de faire le calcul 1 + 1 + ... + 1 (n fois) (à l'associativité près). Et ce calcul nécessite n push, et (n - 1) opérations "Addition" d'où 2*n - 1 transitions.

