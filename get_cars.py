#!/usr/bin/env python
"""Get 4Runner vehicles from Toyota's inventory."""
import json
import uuid

import pandas as pd
import requests

# Set this to True to query local data instead of Toyota's API.
QUERY_LOCAL_DATA = False

GRAPHQL_QUERY = """query {
  locateVehiclesByZip(
    zipCode: "78729"
    brand: "TOYOTA"
    pageNo: %d
    pageSize: 250
    seriesCodes: "4runner"
    distance: 20000
    leadid: "%s"
  ) {
    pagination {
      pageNo
      pageSize
      totalPages
      totalRecords
    }
    vehicleSummary {
      vin
      stockNum
      brand
      marketingSeries
      year
      isTempVin
      dealerCd
      dealerCategory
      distributorCd
      holdStatus
      weightRating
      isPreSold
      dealerMarketingName
      dealerWebsite
      isSmartPath
      distance
      isUnlockPriceDealer
      transmission {
        transmissionType
      }
      price {
        advertizedPrice
        nonSpAdvertizedPrice
        totalMsrp
        sellingPrice
        dph
        dioTotalMsrp
        dioTotalDealerSellingPrice
        dealerCashApplied
        baseMsrp
      }
      options {
        optionCd
        marketingName
        optionType
        dealerSellingPrice
        msrp
      }
      model {
        modelCd
        marketingName
        marketingTitle
      }
      intColor {
        marketingName
      }
      extColor {
        marketingName
      }
      eta {
        currFromDate
        currToDate
      }
      engine {
        engineCd
        name
      }
      drivetrain {
        code
        title
      }
      family
      cab {
        code
        title
      }
      bed {
        code
        title
      }
    }
  }
}
"""


def query_toyota(page_number):
    """Query Toyota for a page of vehicles."""
    print(f"Getting page {page_number}")
    url = "https://api.search-inventory.toyota.com/graphql"
    headers = {
        "referrer": "https://www.toyota.com/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0",
        "accept": "*/*",
    }
    json_post = {"query": GRAPHQL_QUERY % (page_number, str(uuid.uuid4()))}
    resp = requests.post(url, json=json_post, headers=headers)

    return resp.json()["data"]["locateVehiclesByZip"]["vehicleSummary"]


def query_local_data():
    """Query local data for a page of vehicles."""
    return pd.json_normalize(json.load(open("vehicles_raw.json", "r")))


def get_all_vehicles():
    """Get all vehicles from Toyota."""
    df = pd.DataFrame()
    page_number = 1
    while True:
        try:
            vehicles = query_toyota(page_number)
        except Exception as exc:
            print(f"Error: {exc}")
            break

        if vehicles:
            df = pd.concat([df, pd.json_normalize(vehicles)])
            page_number += 1
            continue

        break

    return df


def cleanup_columns(df):
    """Replace data in columns."""
    df["Model"] = df["Model"].str.replace("4Runner ", "")
    df["Model"] = df["Model"].str.replace("40th Anniversary Special Edition", "40th")
    df["Color"] = df["Color"].str.replace(" [extra_cost_color]", "", regex=False)

    # Calculate the dealer's final price.
    df["Dealer Price"] = df["Base MSRP"] + df["price.dioTotalDealerSellingPrice"]
    df.drop(columns=["price.dioTotalDealerSellingPrice"], inplace=True)
    return df


def translate_status(df):
    """Translate the vehicle shipping status into useful values."""
    statuses = {
        "A": "Factory to port",
        "F": "Port to dealer",
        "G": "At dealer",
    }
    return df.replace({"Shipping Status": statuses})


def translate_presold(df):
    """Translate the vehicle presold status into useful values."""
    statuses = {
        None: "No",
        False: "No",
        True: "Yes",
    }
    return df.replace({"Pre-Sold": statuses})


def make_view(df):
    """Create a view of the dataframe with the columns we care about."""
    df = df[
        [
            "vin",
            "dealerCategory",
            "price.baseMsrp",
            "price.dioTotalDealerSellingPrice",
            "isPreSold",
            "holdStatus",
            "year",
            "model.marketingName",
            "extColor.marketingName",
            "dealerMarketingName",
        ]
    ].copy()
    return df.rename(
        columns={
            "vin": "VIN",
            "price.baseMsrp": "Base MSRP",
            "model.marketingName": "Model",
            "extColor.marketingName": "Color",
            "dealerCategory": "Shipping Status",
            "dealerMarketingName": "Dealer",
            "isPreSold": "Pre-Sold",
            "holdStatus": "Hold Status",
            "year": "Year",
        }
    )


if QUERY_LOCAL_DATA:
    raw_df = query_local_data()
else:
    raw_df = get_all_vehicles()

df = make_view(raw_df)
df = cleanup_columns(df)
df = translate_status(df)
df = translate_presold(df)

# Get column ordering just right.
df = df.reindex(
    columns=[
        "VIN",
        "Model",
        "Year",
        "Color",
        "Base MSRP",
        "Dealer Price",
        "Shipping Status",
        "Hold Status",
        "Pre-Sold",
        "Dealer",
    ]
)

# Sort by VIN to avoid lots of repo churn.
df = df.sort_values(["VIN"], ascending=[True])
raw_df = raw_df.sort_values(["vin"], ascending=[True])

# Write to the markdown file.
df.info()
df.to_markdown("vehicles.md", index=False)

# Write JSON files, too.
df.to_json("vehicles.json", orient="records", indent=2)
raw_df.to_json("vehicles_raw.json", orient="records", indent=2)
