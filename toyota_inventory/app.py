"""Main flask application."""
import json

from flask import Flask, render_template
import pandas as pd

app = Flask("toyota_inventory")


def load_vehicles():
    """Load the vehicles from the CSV."""
    if not hasattr(app, "vehicles"):
        with open("vehicles_raw.json", "r") as fileh:
            df = pd.json_normalize(json.load(fileh))
            df["price.dioTotalDealerSellingPrice"] = df[
                "price.dioTotalDealerSellingPrice"
            ].fillna(value=0)
            app.vehicles = df

    return app.vehicles


def all_colors():
    """Get the 4Runner colors."""
    color_key = "extColor.marketingName"
    df = load_vehicles()
    df[color_key] = df[color_key].str.replace(" [extra_cost_color]", "", regex=False)
    df = df.groupby([color_key])[color_key].count()
    return df.to_dict()


def all_models():
    """Get the 4Runner model names."""
    model_key = "model.marketingName"
    df = load_vehicles()
    df[model_key] = df[model_key].str.replace("4Runner ", "")
    df = load_vehicles().groupby([model_key])[model_key].count()
    return df.to_dict()


def all_statuses():
    """Get all delivery statuses"""
    statuses = {"A": "Factory to port", "F": "Port to dealer", "G": "At dealer"}
    df = load_vehicles().replace({"dealerCategory": statuses})
    df = df.groupby(["dealerCategory"])["dealerCategory"].count()
    return df.to_dict()


@app.context_processor
def inject_global_template_variables():
    return dict(
        models=all_models(),
        colors=all_colors(),
        statuses=all_statuses(),
        total_vehicles=len(load_vehicles()),
    )


@app.route("/")
def index():
    """Show the main page."""
    return render_template("index.html", doot="doot")


@app.route("/all/")
def all_vehicles():
    """Show vehicles by color."""
    return render_template("listing.html", vehicles=load_vehicles())


@app.route("/color/<color>/")
def vehicles_by_color(color):
    """Show vehicles by color."""
    orig_color = color.replace("_", " ")
    df = load_vehicles()
    df = df[df["extColor.marketingName"] == orig_color]
    return render_template("listing.html", color=orig_color, vehicles=df)


@app.route("/model/<model>/")
def vehicles_by_model(model):
    """Show vehicles by model."""
    orig_model = model.replace("_", " ")
    df = load_vehicles()
    df = df[df["model.marketingName"] == orig_model]
    return render_template("listing.html", model=orig_model, vehicles=df)


@app.route("/status/<status>/")
def vehicles_by_status(status):
    """Show vehicles by shipping status."""
    orig_status = status.replace("_", " ")
    df = load_vehicles()
    df = df[df["dealerCategory"] == orig_status]
    return render_template("listing.html", status=orig_status, vehicles=df)


def main():
    """Run the flask app."""
    app.run(debug=True, host="0.0.0.0")
