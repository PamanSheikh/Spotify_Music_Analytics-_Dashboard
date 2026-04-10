import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import kagglehub
import os
from functools import lru_cache

# -------------------------------
# Load Dataset using KaggleHub
# -------------------------------
@lru_cache(maxsize=1)
def load_data():
    path = kagglehub.dataset_download("maharshipandya/-spotify-tracks-dataset")
    print("Dataset downloaded at:", path)

    files = os.listdir(path)
    csv_file = [f for f in files if f.endswith(".csv")][0]

    df = pd.read_csv(os.path.join(path, csv_file))
    df = df.dropna()

    return df

df = load_data()

# Limit genres (avoid clutter)
top_genres = df["track_genre"].value_counts().nlargest(10).index
df = df[df["track_genre"].isin(top_genres)]

# -------------------------------
# App Setup
# -------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# -------------------------------
# Layout
# -------------------------------
app.layout = dbc.Container([

    html.H1("🎧 Spotify Music Analytics Dashboard",
            className="text-center text-light mb-4"),

    # Filters
    dbc.Row([

        dbc.Col([
            html.Label("Select Genre"),
            dcc.Dropdown(
                options=[{"label": g, "value": g} for g in sorted(df["track_genre"].unique())],
                multi=True,
                id="genre-filter",
                placeholder="Choose genre"
            )
        ], width=4),

        dbc.Col([
            html.Label("Popularity Range"),
            dcc.RangeSlider(
                min=int(df["popularity"].min()),
                max=int(df["popularity"].max()),
                value=[int(df["popularity"].min()), int(df["popularity"].max())],
                marks={0: "0", 50: "50", 100: "100"},
                id="popularity-slider"
            )
        ], width=8)

    ], className="mb-4"),

    # Graphs Row 1
    dbc.Row([
        dbc.Col(dcc.Graph(id="genre-pie"), width=6),
        dbc.Col(dcc.Graph(id="scatter-plot"), width=6)
    ]),

    # Graphs Row 2
    dbc.Row([
        dbc.Col(dcc.Graph(id="top-artists"), width=6),
        dbc.Col(dcc.Graph(id="duration-hist"), width=6)
    ])

], fluid=True)


# -------------------------------
# Callback
# -------------------------------
@app.callback(
    [
        Output("genre-pie", "figure"),
        Output("scatter-plot", "figure"),
        Output("top-artists", "figure"),
        Output("duration-hist", "figure"),
    ],
    [
        Input("genre-filter", "value"),
        Input("popularity-slider", "value")
    ]
)
def update_graphs(selected_genre, popularity_range):

    dff = df[
        (df["popularity"] >= popularity_range[0]) &
        (df["popularity"] <= popularity_range[1])
    ]

    if selected_genre:
        dff = dff[dff["track_genre"].isin(selected_genre)]

    # Genre Pie Chart
    pie = px.pie(
        dff,
        names="track_genre",
        title="Genre Distribution"
    )

    # Scatter Plot
    scatter = px.scatter(
        dff,
        x="danceability",
        y="energy",
        size="popularity",
        color="track_genre",
        hover_data=["track_name"],
        title="Danceability vs Energy"
    )

    # Top Artists
    top_artists = (
        dff.groupby("artists")["popularity"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    bar = px.bar(
        top_artists,
        x="artists",
        y="popularity",
        title="Top 10 Artists"
    )
    bar.update_layout(xaxis_tickangle=-45)

    # Duration Histogram
    hist = px.histogram(
        dff,
        x="duration_ms",
        nbins=30,
        title="Song Duration Distribution"
    )

    return pie, scatter, bar, hist


# -------------------------------
# Run Server
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)