# Glossaire MTG / Commander — sémantique pour la classification de cartes

Ce document définit les catégories utilisées pour classifier les cartes
d'un deck Commander. Une carte peut appartenir à plusieurs catégories à la
fois.

## Ramp (accélération de mana)

Une carte de ramp augmente la quantité de mana disponible plus vite que
le rythme normal d'un terrain par tour, ou fixe la couleur de mana
disponible de façon significative. Exemples de mécanismes :

- Mettre un terrain supplémentaire en jeu (ex : Rampant Growth,
  Cultivate, Farseek, Kodama's Reach).
- Créer un permanent qui produit du mana sans être un terrain (ex :
  mana rocks comme Sol Ring, Arcane Signet, Signets ; mana dorks comme
  Llanowar Elves, Birds of Paradise).
- Réduire le coût d'invocation d'autres sorts de façon générale (ex :
  Herald's Horn, Cost reducers).
- Rituels ponctuels de mana (ex : Dark Ritual) comptent comme ramp
  seulement s'ils servent à jouer des permanents plus tôt ; utilisés
  uniquement pour un combo, ils comptent plutôt comme pièce de combo.

Ne compte PAS comme ramp : une simple pioche de terrain sans mise en jeu
immédiate (ex : un cantrip qui pioche une carte, même si le joueur pioche
un terrain — c'est de la pioche, pas du ramp), les terrains basiques
eux-mêmes.

## Removal (retrait d'une menace)

Une carte de removal retire, neutralise ou nie durablement une menace
adverse (créature, planeswalker, permanent problématique). Deux
sous-types à noter dans le champ `note` si pertinent :

- Removal ciblé : détruit, exile, contre, réduit à néant ou vole un
  permanent ou un sort précis (ex : Swords to Plowshares, Go for the
  Throat, Counterspell visant un sort dangereux, Beast Within).
- Board wipe / removal de masse : affecte tous les permanents d'un type
  donné (ex : Wrath of God, Toxic Deluge, Cyclonic Rift en mode overload).

Ne compte pas comme removal une carte qui inflige seulement des dégâts
au joueur, ou un simple combat de créatures sans effet de carte dédié.

## Card draw / pioche (avantage de cartes)

Une carte de pioche procure un avantage net de cartes en main, au-delà
de la pioche normale d'un tour. Exemples :

- Pioche directe (ex : Divination, Fact or Fiction, Mulldrifter).
- Engines de pioche répétée (ex : Rhystic Study, Phyrexian Arena,
  Guardian Project).
- Card advantage indirecte comme un impulse draw (ex : "exile the top
  card, you may play it") compte aussi comme pioche.

Ne compte pas comme pioche un simple effet de "regardez le dessus de
votre bibliothèque" sans possibilité de le jouer ou de le garder.

## Win condition (condition de victoire)

Une carte qui constitue une des façons principales dont le deck compte
gagner la partie, par exemple :

- Une menace de dégâts directs ou de combat qui termine la partie une
  fois établie (gros finisher, Voltron sur la commandant, équipe de
  tokens en masse).
- Une pièce de combo qui, combinée à d'autres cartes du deck, gagne la
  partie ou génère un avantage écrasant (mana infini, dégâts infinis,
  mill infini).
- Un effet alternatif de victoire (ex : Thassa's Oracle, Laboratory
  Maniac avec un mill deck, Approach of the Second Sun).

Une carte de removal ou de ramp peut aussi être une pièce de win
condition si elle est un composant identifié d'un combo de victoire du
deck ; l'indiquer dans le champ `note`.

## Archétypes courants (vocabulaire, voir aussi archetypes.md)

Aristocrats, Spellslinger, Reanimator, Voltron, Group Hug, Group Slug,
Stax, Tokens go-wide, Aggro, Midrange, Control, Combo, Landfall, Tribal,
Superfriends (planeswalkers), Enchantress, Artifacts/Affinity, Lands
matter, Graveyard value, Mill.

## Pacing / tour moyen de mise en place

Le "pacing" d'un deck est le tour moyen auquel son plan de jeu principal
devient opérationnel (première win condition crédible sur le champ, ou
premier gros tour d'engine). Un deck avec beaucoup de ramp à 1-2 mana et
un plan de jeu bon marché aura un pacing plus rapide (tour 4-6) ; un
deck qui a besoin de stabiliser son mana et d'accumuler des ressources
avant d'agir aura un pacing plus tardif (tour 8+).
