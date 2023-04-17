"""Main flask application."""
from datetime import datetime
import json

from flask import Flask, render_template
import pandas as pd

app = Flask("toyota_inventory")


def load_vehicles():
    """Load the vehicles from the CSV."""
    if not hasattr(app, "vehicles"):
        with open("4runners.json", "r") as fileh:
            df = pd.json_normalize(json.load(fileh))

            # Cache the value.
            app.vehicles = df

    return app.vehicles


def all_colors():
    """Get the 4Runner colors."""
    df = load_vehicles()
    groupby_key = "Color"
    df = df.groupby([groupby_key])[groupby_key].count().reset_index(name="Count")
    df["Percentage"] = 100 * df["Count"] / df["Count"].sum()
    return df


def all_models():
    """Get the 4Runner model names."""
    df = load_vehicles()
    groupby_key = "Model"
    df = df.groupby([groupby_key])[groupby_key].count().reset_index(name="Count")
    df["Percentage"] = 100 * df["Count"] / df["Count"].sum()
    return df


def all_statuses():
    """Get all delivery statuses."""
    df = load_vehicles()
    groupby_key = "Shipping Status"
    df = df.groupby([groupby_key])[groupby_key].count().reset_index(name="Count")
    df["Percentage"] = 100 * df["Count"] / df["Count"].sum()
    return df


def all_states():
    """Get all dealer states."""
    df = load_vehicles()
    groupby_key = "Dealer State"
    df = df.groupby([groupby_key])[groupby_key].count().reset_index(name="Count")
    df["Percentage"] = 100 * df["Count"] / df["Count"].sum()
    return df


@app.context_processor
def inject_global_template_variables():
    return dict(
        now=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S %Z"),
        colors=all_colors(),
        models=all_models(),
        statuses=all_statuses(),
        states=all_states(),
        total_vehicles=len(load_vehicles()),
    )


@app.route("/")
def index():
    """Show the main page."""
    return render_template("index.html")


@app.route("/all/")
def all_vehicles():
    """Show vehicles by color."""
    return render_template("listing.html", vehicles=load_vehicles())


@app.route("/color/<color>/")
def vehicles_by_color(color):
    """Show vehicles by color."""
    orig_color = color.replace("_", " ")
    df = load_vehicles()
    df = df[df["Color"] == orig_color].sort_values("Dealer Price")
    return render_template("listing.html", color=orig_color, vehicles=df)


@app.route("/model/<model>/")
def vehicles_by_model(model):
    """Show vehicles by model."""
    orig_model = model.replace("_", " ")
    df = load_vehicles()
    df = df[df["Model"] == orig_model].sort_values("Dealer Price")
    return render_template("listing.html", model=orig_model, vehicles=df)


@app.route("/state/<state>/")
def vehicles_by_state(state):
    """Show vehicles by state."""
    df = load_vehicles()
    df = df[df["Dealer State"] == state].sort_values("Dealer Price")
    return render_template("listing.html", state=state, vehicles=df)


@app.route("/status/<status>/")
def vehicles_by_status(status):
    """Show vehicles by shipping status."""
    orig_status = status.replace("_", " ")
    df = load_vehicles()
    df = df[df["Shipping Status"] == orig_status].sort_values("Dealer Price")
    return render_template("listing.html", status=orig_status, vehicles=df)


def main():
    """Run the flask app."""
    app.run(debug=True, host="0.0.0.0")
