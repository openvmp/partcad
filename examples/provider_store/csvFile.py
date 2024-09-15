import csv
from datetime import datetime, timedelta, timezone
import sys

NOW = datetime.now(timezone.utc)

stock = {}


def load():
    global stock, request

    with open(request["parameters"]["file"], newline="\n") as csvfile:
        reader = csv.DictReader(csvfile, lineterminator="\n")
        for row in reader:
            stock[(row["vendor"], row["sku"])] = (
                int(row["count"]),
                float(row["price"]),
            )


if not "request" in globals():
    request = {
        "api": "caps",
    }


if __name__ == "caps":
    raise Exception("Not suported by stores")

elif __name__ == "avail":
    load()

    vendor = request["vendor"]
    sku = request["sku"]
    count_per_sku = request["count_per_sku"]
    count = request["count"]

    if (vendor, sku) in stock:
        output = {
            "available": stock[(vendor, sku)][0] * count_per_sku >= count,
            "count": stock[(vendor, sku)][0],
            "price": stock[(vendor, sku)][1],
        }
    else:
        output = {
            "available": False,
        }

elif __name__ == "quote":
    parts = request["cart"]["parts"]

    load()

    price = 0
    for part_spec in parts.values():
        vendor = part_spec["vendor"]
        sku = part_spec["sku"]
        count_per_sku = part_spec["count_per_sku"]
        count = part_spec["count"]

        available = stock[(vendor, sku)][0] * count_per_sku
        if available < part_spec["count"]:
            raise Exception("Not enough stock")

        items = (count + count_per_sku - 1) // count_per_sku
        price += stock[(vendor, sku)][1] * float(items)

    output = {
        "qos": request["cart"]["qos"],
        "price": price,
        "expire": (NOW + timedelta(hours=1)).timestamp(),
        "cartId": "123456",
        "etaMin": (NOW + timedelta(hours=1)).timestamp(),
        "etaMax": (NOW + timedelta(hours=2)).timestamp(),
    }

elif __name__ == "order":
    raise Exception("Not implemented")

else:
    raise Exception("Unknown API: {}".format(__name__))
