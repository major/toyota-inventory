#!/usr/bin/env python
"""Get 4Runner vehicles from Toyota's inventory."""
import json
import sys

import pandas as pd
import requests

GRAPHQL_QUERY = """query {
  locateVehiclesByZip(
    zipCode: "78108"
    brand: "TOYOTA"
    pageNo: %d
    pageSize: 250
    seriesCodes: "4runner"
    distance: 20000
    leadid: "c1a95bb1-0f55-42f9-994a-ba958fdefba4"
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


def pretty_currency(x):
    return "${:.1f}K".format(x / 1000)


def query_toyota(page_number):
    """Query Toyota for a page of vehicles."""
    print(f"Getting page {page_number}")
    url = "https://api.search-inventory.toyota.com/graphql"
    headers = {
        "referrer": "https://www.toyota.com/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0",
        "accept": "*/*",
    }
    json_post = {"query": GRAPHQL_QUERY % page_number}
    resp = requests.post(url, json=json_post, headers=headers)

    return resp.json()["data"]["locateVehiclesByZip"]["vehicleSummary"]


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


def filter_columns(df):
    """Replace data in columns."""
    df["Model"] = df["Model"].str.replace("4Runner ", "")
    df["Model"] = df["Model"].str.replace("40th Anniversary Special Edition", "40th")
    df["Color"] = df["Color"].str.replace(" [extra_cost_color]", "", regex=False)

    df["MSRP"] = df["MSRP"].apply(pretty_currency)

    df["Dealer"] = "[" + df["dealerMarketingName"] + "](" + df["dealerWebsite"] + ")"
    df.drop(columns=["dealerMarketingName", "dealerWebsite"], inplace=True)
    return df


def make_view(df):
    """Create a view of the dataframe with the columns we care about."""
    df = df[
        [
            "vin",
            "price.totalMsrp",
            "model.marketingName",
            "extColor.marketingName",
            "dealerMarketingName",
            "dealerWebsite",
        ]
    ].copy()
    return df.rename(
        columns={
            "vin": "VIN",
            "price.totalMsrp": "MSRP",
            "model.marketingName": "Model",
            "extColor.marketingName": "Color",
        }
    )


def remove_presold(df):
    """Remove any vehicles which are already sold."""
    return df[df.isPreSold == False]


df = get_all_vehicles()
df = remove_presold(df)
df = make_view(df)
df = filter_columns(df)

# Sort by model name then by MSRP.
df = df.sort_values(["Model", "MSRP"], ascending=[True, True])

# Write to the markdown file.
df.info()
df.to_markdown("vehicles.md", index=False)
