import pandas as pd


def calculate_route_index(df, base_date, current_date):
    base_data = df[df["date"] == base_date]
    current_data = df[df["date"] == current_date]

    base_prices = base_data.groupby("route")["total_fare"].mean()
    current_prices = current_data.groupby("route")["total_fare"].mean()

    route_indices = (current_prices / base_prices) * 100

    return route_indices


def calculate_lead_time_index(df, base_date, current_date):
    base_data = df[df["date"] == base_date]
    current_data = df[df["date"] == current_date]

    base_prices = base_data.groupby("lead_time")["total_fare"].mean()
    current_prices = current_data.groupby("lead_time")["total_fare"].mean()

    lead_time_indices = (current_prices / base_prices) * 100

    return lead_time_indices


def calculate_weighted_national_index(route_indices, weights_df):
    weights = weights_df.set_index("route")["weight"]

    common_routes = route_indices.index.intersection(weights.index)

    weighted_sum = sum(
        route_indices[route] * weights[route]
        for route in common_routes
    )

    total_weight = sum(
        weights[route]
        for route in common_routes
    )

    national_index = weighted_sum / total_weight

    return national_index


def calculate_route_trend(df, route):
    route_data = df[df["route"] == route]

    trend = route_data.groupby("date")["total_fare"].mean()

    return trend

def calculate_historical_index(df, weights_df, base_date=None):
    available_dates = sorted(df["date"].unique())

    if len(available_dates) == 0:
        return {}

    if base_date is None:
        base_date = available_dates[0]

    historical_index = {}

    for current_date in available_dates:
        route_indices = calculate_route_index(
            df,
            base_date,
            current_date
        )

        national_index = calculate_weighted_national_index(
            route_indices,
            weights_df
        )

        historical_index[current_date] = round(
            float(national_index),
            2
        )

    return historical_index

def calculate_percentage_change(previous_value, current_value):
    if previous_value == 0:
        return 0

    return (
        (current_value - previous_value)
        / previous_value
    ) * 100