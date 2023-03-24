# Toyota 4Runner Inventory

_DISCLAIMER: Not affiliated with Toyota in any way._

I've been looking for a good deal on a 4Runner for a while, but the dealer markup is
crazy. I stumbled upon
[kissmygritts'](https://github.com/kissmygritts/flatdata-vehicle-inventory) work on
Reddit and thought about making an inventory grabber of my own, except with GraphQL
instead. Toyota uses a GraphQL lookup when you [search their
inventory](https://www.toyota.com/search-inventory/).

The script in the [toyota-inventory](https://github.com/major/toyota-inventory)
repository does the following:

1. Query the GraphQL endpoint for as much inventory in the US as possible
2. Narrow down the fields to the most important ones
3. Filter some data in some of the fields to make it easier to read
4. Exclude vehicles which are already pre-sold _(on the way to the dealer, but someone's
   in the process of buying them)_
4. Sorts the data based on model, then MSRP

The script runs daily and updates this page. Enjoy! 👋

----





