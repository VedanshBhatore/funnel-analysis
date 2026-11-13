"""Phase 4: sample-size / duration calculations for the 3 A/B tests in
docs/experiments.md. Baselines come straight from data/02_funnel.csv and
data/03_funnel_segments.csv (view_item -> add_to_cart step) and
data/05_product_funnel.csv (category_view_to_cart rows) -- no made-up numbers.
Run directly to print the numbers that appear in docs/experiments.md.
"""
import math

import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

DAYS_IN_WINDOW = 92  # 2020-11-01 .. 2021-01-31, confirmed in docs/data-profile.md

power_analysis = NormalIndPower()


def solve(name, baseline, mde_abs, daily_eligible):
    target = baseline + mde_abs
    effect_size = proportion_effectsize(baseline, target)
    n_per_arm = power_analysis.solve_power(
        effect_size=effect_size, alpha=0.05, power=0.8, ratio=1.0, alternative="two-sided"
    )
    n_per_arm_ceil = math.ceil(n_per_arm)
    total_n = n_per_arm_ceil * 2
    duration_days = math.ceil(total_n / daily_eligible)
    print(f"\n=== {name} ===")
    print(f"baseline p1 = {baseline:.4%}")
    print(f"target   p2 = {target:.4%}  (MDE = {mde_abs*100:.2f} pp absolute, {(mde_abs/baseline)*100:.1f}% relative)")
    print(f"effect size (Cohen's h) = {effect_size:.4f}")
    print(f"n per arm = {n_per_arm:.1f} -> ceil {n_per_arm_ceil}")
    print(f"total sample (both arms) = {total_n}")
    print(f"daily eligible traffic = {daily_eligible:.1f} / day")
    print(f"estimated duration = {duration_days} days (~{duration_days/7:.1f} weeks)")
    return {
        "name": name, "baseline": baseline, "target": target, "effect_size": effect_size,
        "n_per_arm": n_per_arm_ceil, "total_n": total_n,
        "daily_eligible": daily_eligible, "duration_days": duration_days,
    }


def main():
    funnel = pd.read_csv(DATA / "02_funnel.csv").set_index("step_name")
    segments = pd.read_csv(DATA / "03_funnel_segments.csv")
    product = pd.read_csv(DATA / "05_product_funnel.csv")

    # Exp 1: site-wide view_item -> add_to_cart baseline
    view_item_sessions = funnel.loc["view_item", "sessions"]
    add_to_cart_sessions = funnel.loc["add_to_cart", "sessions"]
    baseline_1 = add_to_cart_sessions / view_item_sessions

    # Exp 2: cpc traffic_medium segment, same step
    cpc = segments[(segments.segment_type == "traffic_medium") & (segments.segment_value == "cpc")]
    cpc_view = cpc[cpc.step_order == 2]["sessions"].iloc[0]
    cpc_cart = cpc[cpc.step_order == 3]["sessions"].iloc[0]
    baseline_2 = cpc_cart / cpc_view

    # Exp 3: pooled weak categories (Accessories/, Backpacks/, Water Bottles/)
    cat = product[product.query_type == "category_view_to_cart"].set_index("segment_label")
    weak_cats = ["Accessories/", "Backpacks/", "Water Bottles/"]
    weak_views = cat.loc[weak_cats, "metric_1"].sum()
    weak_carts = cat.loc[weak_cats, "metric_2"].sum()
    baseline_3 = weak_carts / weak_views

    results = [
        solve("Exp 1: Simplify PDP add-to-cart CTA (site-wide)",
              baseline_1, 0.02, view_item_sessions / DAYS_IN_WINDOW),
        solve("Exp 2: Paid-search (cpc) landing-page relevance fix",
              baseline_2, 0.05, cpc_view / DAYS_IN_WINDOW),
        solve("Exp 3: Shipping-cost transparency on weak categories (Accessories/Backpacks/Water Bottles)",
              baseline_3, 0.022, weak_views / DAYS_IN_WINDOW),
    ]
    pd.DataFrame(results).to_csv(DATA / "power_analysis_results.csv", index=False)
    print(f"\nWrote {DATA / 'power_analysis_results.csv'}")


if __name__ == "__main__":
    main()
