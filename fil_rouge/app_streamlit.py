"""Tableau de bord hebdomadaire pour analyser mes parties d'échecs."""

import plotly.express as px
import streamlit as st

from data import familles, load_coups, load_data

st.set_page_config(
    page_title="Mes parties d'échecs",
    page_icon="♟",
    layout="wide",
)
print("relance")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stMetric"] {
        background: #f7f8fc;
        border: 1px solid #e8ecf3;
        border-radius: 0.8rem;
        padding: 1rem 1.2rem;
    }
    [data-testid="stMetricLabel"] { color: #53627a; }
    section[data-testid="stSidebar"] { border-right: 1px solid #e8ecf3; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Chargement de vos parties...")
def charger_donnees():
    return load_data(), load_coups()


df, coups = charger_donnees()
date_min = df["date_jeu"].dt.date.min()
date_max = df["date_jeu"].dt.date.max()

st.title("Où est-ce que je peux progresser aux échecs ?")
st.caption(
    "Explorez vos résultats par cadence, période et couleur pour repérer "
    "les ouvertures et les phases à travailler."
)

with st.sidebar:
    st.header("Filtres")
    st.caption("Les graphiques et indicateurs se mettent à jour à chaque sélection.")

    cadences = sorted(df["cadence"].dropna().unique().tolist())
    cadences_choisies = st.multiselect(
        "Cadence",
        options=cadences,
        default=cadences,
        key="cadences",
        help="« Aucune » correspond aux parties sans cadence renseignée.",
    )
    periode = st.date_input(
        "Période",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
        format="DD/MM/YYYY",
        key="periode",
    )
    couleurs = st.multiselect(
        "Couleur jouée",
        options=["white", "black"],
        default=["white", "black"],
        format_func=lambda couleur: "Blancs" if couleur == "white" else "Noirs",
        key="couleurs",
    )
    n_min = st.slider(
        "Parties minimum par ouverture",
        min_value=1,
        max_value=50,
        value=10,
        key="n_min",
        help="Masque les ouvertures jouées trop rarement pour être significatives.",
    )

if not isinstance(periode, (tuple, list)) or len(periode) != 2:
    st.warning("Choisissez une date de début et une date de fin pour afficher l'analyse.")
    st.stop()

debut, fin = periode
vue = df.loc[
    df["cadence"].isin(cadences_choisies)
    & df["date_jeu"].dt.date.between(debut, fin)
    & df["couleur"].isin(couleurs)
].copy()

if vue.empty:
    st.warning("Aucune partie ne correspond à ces filtres. Modifiez la sélection.")
    st.stop()

ids_parties = vue["partie_id"]
coups_vue = coups.loc[coups["partie_id"].isin(ids_parties)]

st.subheader("Votre bilan")
metriques = st.columns(3)
metriques[0].metric("Parties jouées", f"{len(vue):,}".replace(",", " "))
metriques[1].metric("Score moyen", f"{vue['score'].mean():.0%}")
metriques[2].metric(
    "Gaffes par partie",
    f"{vue['gaffes_joueur'].mean():.2f}".replace(".", ","),
)

st.subheader("Ouvertures et phases à travailler")
col_familles, col_phases = st.columns(2, gap="large")

with col_familles:
    st.markdown("#### Score par ouverture")
    resume_familles = familles(vue, min_n=n_min)
    if resume_familles.empty:
        st.info("Aucune ouverture ne dépasse le minimum de parties choisi.")
    else:
        figure_familles = px.bar(
            resume_familles,
            x="score",
            y="famille",
            color="score",
            hover_data={"n": True, "gaffes": ":.2f"},
            labels={
                "score": "Score moyen",
                "famille": "Famille d'ouvertures",
                "n": "Parties",
                "gaffes": "Gaffes par partie",
            },
            color_continuous_scale=["#d96c5f", "#f3c677", "#55a890"],
            range_color=[0, 1],
        )
        figure_familles.update_layout(
            height=440,
            margin={"l": 8, "r": 8, "t": 16, "b": 8},
            coloraxis_showscale=False,
            xaxis_tickformat=".0%",
            xaxis_range=[0, 1],
        )
        figure_familles.update_yaxes(
            categoryorder="array",
            categoryarray=resume_familles["famille"].tolist(),
            autorange="reversed",
        )
        st.plotly_chart(
            figure_familles,
            width="stretch",
            config={"displayModeBar": False},
            key="graphique_familles",
        )
        st.caption(
            f"Les ouvertures les moins performantes sont en haut. "
            f"Seuil : {n_min} parties minimum."
        )

with col_phases:
    st.markdown("#### Où tombent les gaffes ?")
    noms_phases = {
        "opening": "Ouverture",
        "middlegame": "Milieu de partie",
        "endgame": "Finale",
    }
    ordre_phases = list(noms_phases.values())
    resume_phases = (
        coups_vue.loc[coups_vue["jugement"].eq("blunder"), "phase"]
        .map(noms_phases)
        .value_counts()
        .reindex(ordre_phases, fill_value=0)
        .rename_axis("phase")
        .reset_index(name="gaffes")
    )
    figure_phases = px.bar(
        resume_phases,
        x="phase",
        y="gaffes",
        color="phase",
        category_orders={"phase": ordre_phases},
        labels={"phase": "Phase de la partie", "gaffes": "Nombre de gaffes"},
        color_discrete_sequence=["#6687c4", "#e7a64b", "#55a890"],
    )
    figure_phases.update_layout(
        height=440,
        margin={"l": 8, "r": 8, "t": 16, "b": 8},
        showlegend=False,
    )
    st.plotly_chart(
        figure_phases,
        width="stretch",
        config={"displayModeBar": False},
        key="graphique_phases",
    )
    st.caption(
        "Nombre de coups classés « gaffe » dans les parties filtrées, "
        "par phase de la partie."
    )
