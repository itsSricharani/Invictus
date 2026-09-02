import pandas as pd

from pipeline.cleaner import load_and_clean_data
from pipeline.index_calculator import (
    calculate_route_index,
    calculate_weighted_national_index
)


df = load_and_clean_data("data/sample_fares.csv")
weights_df = pd.read_csv("data/route_weights.csv")

route_indices = calculate_route_index(
    df,
    "2026-08-01",
    "2026-08-08"
)

national_index = calculate_weighted_national_index(
    route_indices,
    weights_df
)

print("Route Indices:")
print(route_indices)

print("\nRoute Weights:")
print(weights_df)

print("\nWeighted National APIx:")
print(round(national_index, 2))