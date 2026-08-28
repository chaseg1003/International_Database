import pandas as pd
import mysql.connector
from dynaconf import Dynaconf
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import plotly.express as px

# Load settings
settings = Dynaconf(
    envvar_prefix="DB",
    load_dotenv=True,
    dotenv_path=".env"
)

conn = mysql.connector.connect(
    host=settings.get("host"),
    user=settings.get("user"),
    password=settings.get("password"),
    database=settings.get("database")
)

#Separate dataframes for different statistics
query = "SELECT geo_id, year, fertility_rate FROM country_stats"
df = pd.read_sql(query, conn)
query = "SELECT * FROM country_stats"
df1 = pd.read_sql(query, conn)
query = """select c.geo_id, c.`year`, c.life_expectancy, c.infant_mortality, c.population_density, c.sex_ratio, c.dependency_ratio, f.age_group, f.fertility_rate
from country_stats c
inner join fertility_rates f on c.geo_id = f.geo_id and c.year = f.year;"""
df2 = pd.read_sql(query, conn)
query = "select * from fertility_rates"
df3 = pd.read_sql(query, conn)
conn.close()

year_options = [{"label": str(y), "value": y} for y in sorted(df1["year"].unique())]
country_options = [{"label": geo, "value": geo} for geo in df1["geo_id"].unique()]

age_group_order = [
    "15_19", "20_24", "25_29", "30_34", "35_39", "40_44", "45_49"
]

# Wanted the age groups colors to be in rainbow order to be easier to interpret
age_group_colors = [
    "#e41a1c",  # red
    "#ff7f00",  # orange
    "#e7e72c",  # yellow
    "#4daf4a",  # green
    "#3db7d0",  # turquoise
    "#377eb8",  # blue
    "#984ea3"   # indigo
]

app = Dash()

app.layout = html.Div([
    html.H1("Fertility Rate Trends"),
    dcc.Graph(
        figure=px.line(df, 
            x="year", 
            y="fertility_rate", 
            color="geo_id",
            title="Fertility Rate Over Time by Country",
        )
    ),
    dcc.Dropdown(["life_expectancy", "infant_mortality", "population_density", "sex_ratio", "dependency_ratio"], 
                 "life_expectancy", 
                 id="fertility-dropdown"),
    dcc.Dropdown(year_options, year_options[0]["value"], id="year-dropdown"),
    dcc.Graph(id="fertility_graph"),
    dcc.Dropdown(["life_expectancy", "infant_mortality", "population_density", "sex_ratio", "dependency_ratio"], 
                 "life_expectancy", 
                 id="fertility-dropdown-age"),
    dcc.Dropdown(year_options, year_options[0]["value"], id="year-dropdown-age"),
    dcc.Graph(id="fertility_graph_age_groups"),
    dcc.Dropdown(country_options, country_options[0]["value"], id="country-dropdown"),
    dcc.Graph(id="country_over_time"),
    dcc.Dropdown(country_options, country_options[0]["value"], id="country-dropdown-age"),
    dcc.Graph(id="country_over_time_age_groups")
])

@callback(
    Output("fertility_graph", "figure"),
    Input("fertility-dropdown", "value"),
    Input("year-dropdown", "value")
)
def update_graph(fertility_metric, year):
    filtered_df = df1[df1["year"] == year]
    # Used the absolute value of the sex ratio to make the regression line calculation more accurate
    if fertility_metric == "sex_ratio":
        filtered_df[fertility_metric] = (filtered_df[fertility_metric] - 1).abs()
    # Had the x axis be logarithmic for population density to better visualize the data
    log_x = fertility_metric == "population_density"
    fig = px.scatter(filtered_df, x=fertility_metric, y="fertility_rate", size_max=15, size=None, log_x=log_x, trendline="ols", title=f"Fertility Rate vs {fertility_metric}")
    return fig
@callback(
    Output("fertility_graph_age_groups", "figure"),
    Input("fertility-dropdown-age", "value"),
    Input("year-dropdown-age", "value")
)
def update_fertility_graph_age_groups(fertility_metric, year):
    filtered_df = df2[df2["year"] == year]
    if fertility_metric == "sex_ratio":
        filtered_df[fertility_metric] = (filtered_df[fertility_metric] - 1).abs()
    log_x = fertility_metric == "population_density"
    fig = px.scatter(
        filtered_df,
        x=fertility_metric,
        y="fertility_rate",
        color="age_group",
        size_max=15,
        size=None,
        log_x=log_x,
        trendline="ols",
        title=f"Fertility Rate vs {fertility_metric} by Age Group",
        category_orders={"age_group": age_group_order},
        color_discrete_sequence=age_group_colors
    )
    return fig
@callback(
    Output("country_over_time", "figure"),
    Input("country-dropdown", "value")
)
def update_country_graph(selected_country):
    filtered_df = df1[df1["geo_id"] == selected_country]
    fig = px.line(filtered_df, x="year", y="fertility_rate", title=f"Fertility Rate Over Time for {selected_country}")
    fig.update_layout(xaxis=dict(range=[filtered_df["year"].min(), 2025]))
    # Remove data after 2025 as data after that is just predictions
    fig.data[0].x = [x for x in fig.data[0].x if x <= 2025]
    fig.data[0].y = [y for x, y in zip(fig.data[0].x, fig.data[0].y) if x <= 2025]
    return fig
@callback(
    Output("country_over_time_age_groups", "figure"),
    Input("country-dropdown-age", "value")
)
def update_country_graph_age_groups(selected_country):
    filtered_df = df3[df3["geo_id"] == selected_country]
    fig = px.line(
        filtered_df,
        x="year",
        y="fertility_rate",
        color="age_group",
        title=f"Fertility Rate by Age Group Over Time for {selected_country}",
        category_orders={"age_group": age_group_order},
        color_discrete_sequence=age_group_colors
    )
    fig.update_layout(xaxis=dict(range=[filtered_df["year"].min(), 2025]))
    # Remove data after 2025 for each age group trace
    for trace in fig.data:
        mask = [x <= 2025 for x in trace.x]
        trace.x = [x for x, m in zip(trace.x, mask) if m]
        trace.y = [y for y, m in zip(trace.y, mask) if m]
    return fig

if __name__ == "__main__":
    app.run(debug=True)

