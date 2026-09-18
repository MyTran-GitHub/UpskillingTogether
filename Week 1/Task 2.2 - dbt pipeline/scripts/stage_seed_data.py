"""Prepare the dbt seed files for the initial or complete fixture."""

import argparse
import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"
CUTOFF = "2025-03-31"


def read_csv(name):
    with (ROOT / name).open(newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames, list(reader)


def write_csv(name, fields, rows):
    with (SEEDS / name).open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


parser = argparse.ArgumentParser()
parser.add_argument("batch", choices=("initial", "all"))
args = parser.parse_args()

SEEDS.mkdir(exist_ok=True)
shutil.copyfile(ROOT / "raw_customers.csv", SEEDS / "raw_customers.csv")

order_fields, orders = read_csv("raw_orders.csv")
if args.batch == "initial":
    orders = [order for order in orders if order["order_date"] <= CUTOFF]
write_csv("raw_orders.csv", order_fields, orders)

order_ids = {order["order_id"] for order in orders}
payment_fields, payments = read_csv("raw_payments.csv")
payments = [payment for payment in payments if payment["order_id"] in order_ids]
write_csv("raw_payments.csv", payment_fields, payments)

print(f"{args.batch}: {len(orders)} orders, {len(payments)} payments")
