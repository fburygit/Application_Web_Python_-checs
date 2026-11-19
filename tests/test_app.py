import pandas as pd
import pytest

import data

PARTIES = ["partie_id", "date_jeu", "resultat", "cadence", "couleur", "elo_joueur", "elo_adverse"]


def test_csv_des_parties_se_lisent():
    df = pd.read_csv(data.DATA / "parties.csv")
    assert len(df) > 1000
    assert set(PARTIES) <= set(df.columns)
    assert df["partie_id"].is_unique


def test_csv_des_coups_juges_se_lisent():
    coups = pd.read_csv(data.DATA / "coups_juges.csv")
    assert {"partie_id", "coup", "jugement", "phase"} <= set(coups.columns)


def test_load_data_une_ligne_par_partie():
    df = data.load_data()
    assert df["partie_id"].is_unique
    assert df["score"].isin([0, 0.5, 1]).all()
    assert df["resultat"].isin(["victoire", "nulle", "défaite"]).all()
    assert "aucune" in df["cadence"].unique()
    assert pd.api.types.is_datetime64_any_dtype(df["date_jeu"])
    assert df["heure"].between(0, 23).all()
    assert df["ecart_elo"].equals(df["elo_adverse"] - df["elo_joueur"])


def test_familles_pire_en_premier():
    f = data.familles(data.load_data(), 30)
    assert f["score"].is_monotonic_increasing
    assert f["n"].ge(30).all()


def test_valider_signale_un_resultat_inconnu():
    df = pd.read_csv(data.DATA / "parties.csv")
    df.loc[0, "resultat"] = "inconnu"

    with pytest.raises(ValueError, match="Résultats inconnus"):
        data.valider(df)


def test_valider_signale_les_nombres_lus_comme_du_texte():
    df = pd.read_csv(data.DATA / "parties.csv")
    df["gaffes_joueur"] = df["gaffes_joueur"].astype("string")

    with pytest.raises(ValueError, match="numériques lues comme du texte"):
        data.valider(df)
