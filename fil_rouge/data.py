"""Exo 1 : lire mes parties d'échecs. Environ 25 min.

Question : je joue depuis 2023, je stagne, qu'est-ce que je devrais travailler ?
À produire : un DataFrame propre, prêt pour les figures de l'exo 1 et pour l'appli de l'exo 2.
Les colonnes et leurs pièges sont dans data/echecs/LISEZMOI.md : lisez-le d'abord.
Lancer : uv run python fil_rouge/data.py
"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "echecs"

_COLONNES_REQUISES = {
    "partie_id",
    "date_jeu",
    "cadence",
    "couleur",
    "resultat",
    "elo_joueur",
    "elo_adverse",
    "ouverture_famille",
    "gaffes_joueur",
}
_COLONNES_NUMERIQUES = ("elo_joueur", "elo_adverse", "gaffes_joueur")
_RESULTATS = {"win", "draw", "lose"}


def valider(df: pd.DataFrame) -> pd.DataFrame:
    """Plan B : s'arrêter avec un message clair si le fichier n'a pas la forme attendue.

    Colonnes absentes, colonnes entièrement vides, nombres lus comme du texte,
    identifiant de partie en double, résultat inconnu.
    """
    absentes = sorted(_COLONNES_REQUISES - set(df.columns))
    if absentes:
        raise ValueError(f"Colonnes absentes : {', '.join(absentes)}")

    vides = sorted(col for col in _COLONNES_REQUISES if df[col].isna().all())
    if vides:
        raise ValueError(f"Colonnes entièrement vides : {', '.join(vides)}")

    if df["partie_id"].isna().any() or df["partie_id"].astype("string").str.strip().eq("").any():
        raise ValueError("La colonne partie_id contient un identifiant vide.")
    if df["partie_id"].duplicated().any():
        raise ValueError("La colonne partie_id contient des doublons.")

    non_numeriques = [
        col for col in _COLONNES_NUMERIQUES if not pd.api.types.is_numeric_dtype(df[col])
    ]
    if non_numeriques:
        raise ValueError(
            f"Colonnes numériques lues comme du texte ou non numériques : "
            f"{', '.join(non_numeriques)}"
        )

    resultats = df["resultat"].astype("string").str.strip()
    inconnus = resultats.loc[~resultats.isin(_RESULTATS)]
    if not inconnus.empty:
        valeurs = sorted(inconnus.fillna("<vide>").unique().tolist())
        raise ValueError(f"Résultats inconnus : {', '.join(valeurs)}")

    dates = pd.to_datetime(df["date_jeu"], errors="coerce")
    if dates.isna().any():
        raise ValueError("La colonne date_jeu contient une date vide ou invalide.")

    return df


def load_data() -> pd.DataFrame:
    """Une ligne par partie (data/echecs/parties.csv), validée.

    Ajoutez : le résultat de mon point de vue en français, un score (1, 0,5 ou 0),
    l'année, l'heure, et l'écart d'Elo avec l'adversaire. Une cadence vide veut dire
    « aucune » : ne la laissez pas disparaître des filtres.
    Les exos suivants lisent ces colonnes, gardez ces noms : date_jeu (en datetime),
    resultat (victoire, nulle, défaite), score, annee, heure (UTC), ecart_elo
    (Elo de l'adversaire moins le mien), cadence.
    """
    df = pd.read_csv(DATA / "parties.csv")
    valider(df)

    df["date_jeu"] = pd.to_datetime(df["date_jeu"])
    df["resultat"] = (
        df["resultat"]
        .astype("string")
        .str.strip()
        .map({"win": "victoire", "draw": "nulle", "lose": "défaite"})
    )
    df["score"] = df["resultat"].map({"victoire": 1.0, "nulle": 0.5, "défaite": 0.0})
    df["annee"] = df["date_jeu"].dt.year
    df["heure"] = df["date_jeu"].dt.hour
    df["ecart_elo"] = df["elo_adverse"] - df["elo_joueur"]
    df["cadence"] = df["cadence"].fillna("").astype("string").str.strip().replace("", "aucune")
    return df


def load_coups() -> pd.DataFrame:
    """Un de mes coups jugés mauvais par ligne (data/echecs/coups_juges.csv)."""
    return pd.read_csv(DATA / "coups_juges.csv")


def familles(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Score moyen par famille d'ouvertures, la pire d'abord.

    Colonnes : famille, n (parties), score, gaffes (par partie).
    Sous min_n parties le chiffre ne dit rien : écartez la famille.
    """
    jouables = df.loc[
        df["ouverture_famille"].notna()
        & df["ouverture_famille"].astype("string").str.strip().ne("")
    ]
    resume = (
        jouables.groupby("ouverture_famille", as_index=False)
        .agg(
            n=("partie_id", "size"),
            score=("score", "mean"),
            gaffes=("gaffes_joueur", "mean"),
        )
        .rename(columns={"ouverture_famille": "famille"})
    )
    return (
        resume.loc[resume["n"] >= min_n]
        .sort_values(["score", "famille"])
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    d = load_data()
    print(d.shape)
