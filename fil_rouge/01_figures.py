"""Exo 1 : trois figures. Environ 25 min.

Question : où ce joueur perd-il des points ?
À produire : trois figures Plotly dont le titre dit ce qu'elles montrent.
Lancer : uv run python fil_rouge/01_figures.py
"""

import plotly.express as px

from data import familles, load_coups, load_data

df, coups = load_data(), load_coups()
print(df.shape, coups.shape)

# 1. Le score moyen par famille d'ouvertures, de la pire à la meilleure.
par_famille = familles(df)
figure_familles = px.bar(
    par_famille,
    x="score",
    y="famille",
    hover_data=["n", "gaffes"],
    labels={
        "score": "Score moyen",
        "famille": "Famille d'ouvertures",
        "n": "Parties",
        "gaffes": "Gaffes par partie",
    },
    title="Les familles d'ouvertures où je marque le moins de points",
)
figure_familles.update_yaxes(
    categoryorder="array",
    categoryarray=par_famille["famille"].tolist(),
    autorange="reversed",
)
figure_familles.show()

# 2. Le nombre de gaffes selon la phase de la partie.
noms_phases = {
    "opening": "Ouverture",
    "middlegame": "Milieu de partie",
    "endgame": "Finale",
}
ordre_phases = list(noms_phases.values())
gaffes_par_phase = (
    coups.loc[coups["jugement"].eq("blunder"), "phase"]
    .map(noms_phases)
    .value_counts()
    .reindex(ordre_phases, fill_value=0)
    .rename_axis("phase")
    .reset_index(name="gaffes")
)
figure_phases = px.bar(
    gaffes_par_phase,
    x="phase",
    y="gaffes",
    labels={"phase": "Phase de la partie", "gaffes": "Nombre de gaffes"},
    title="Dans quelle phase mes gaffes tombent-elles ?",
)
figure_phases.show()

# 3. Le score moyen selon l'heure UTC, avec au moins 30 parties par heure.
score_par_heure = (
    df.groupby("heure", as_index=False)
    .agg(score=("score", "mean"), n=("score", "size"))
)
score_par_heure = score_par_heure.loc[score_par_heure["n"] >= 30]
figure_heures = px.bar(
    score_par_heure,
    x="heure",
    y="score",
    hover_data=["n"],
    labels={"heure": "Heure UTC", "score": "Score moyen", "n": "Parties"},
    title="Mon score selon l'heure UTC (au moins 30 parties par heure)",
)
figure_heures.update_xaxes(dtick=1)
figure_heures.show()
