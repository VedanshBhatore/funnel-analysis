# Metric Tree

North Star: **Weekly Purchasing Users** — the number of distinct users who
complete at least one purchase in a given week. It combines both sides of the
business this data surfaces as weak (first-visit conversion) and weaker
(retention): see `docs/insights.md` findings #1 and #4.

```mermaid
graph TD
    NS["North Star:<br/>Weekly Purchasing Users"]

    NS --> SESS["Weekly Sessions"]
    NS --> CONV["Session → Purchase<br/>Conversion Rate (0.79%)"]

    SESS --> NEW["New-visitor sessions<br/>(acquisition)"]
    SESS --> RET["Returning-visitor sessions<br/>(retention)"]

    NEW --> ORGANIC["Organic search"]
    NEW --> PAID["Paid search (cpc)<br/>lowest channel conv. 0.59%"]
    NEW --> REFERRAL["Referral"]
    NEW --> DIRECT["Direct / (none)"]

    RET --> W1["Week-1 return rate<br/>2.47%-10.82%, declined through the holiday peak"]
    RET --> WN["Week 4+ return rate<br/>under 1% for nearly all cohorts"]

    CONV --> STEP1["session_start → view_item<br/>78.79% drop-off"]
    CONV --> STEP2["view_item → add_to_cart<br/>80.21% drop-off (leakiest step)"]
    CONV --> STEP3["add_to_cart → begin_checkout<br/>60.61% drop-off"]
    CONV --> STEP4["begin_checkout → add_shipping_info<br/>0% drop-off (auto-fires)"]
    CONV --> STEP5["add_shipping_info → add_payment_info<br/>35.07% drop-off"]
    CONV --> STEP6["add_payment_info → purchase<br/>26.09% drop-off"]

    NS -.->|"x Average Order Value ($, data/01_kpis_daily.csv)"| REV["Weekly Revenue<br/>(companion metric, not North Star)"]

    style NS fill:#2a78d6,color:#ffffff
    style STEP2 fill:#e34948,color:#ffffff
    style PAID fill:#eda100,color:#0b0b0b
```

**How to read this:** every leaf metric here is computed in this project —
`SESS`/`NEW`/`RET` split from `data/03_funnel_segments.csv` +
`data/04_cohort_retention.csv`; every `CONV` step from `data/02_funnel.csv`;
`AOV`/`REV` from `data/01_kpis_daily.csv`. The red node (`view_item →
add_to_cart`) is the single highest-leverage input — see `docs/insights.md`
and `docs/experiments.md` for why it's the first thing to fix, and the orange
node (paid search) is the second-highest-leverage input on the acquisition
side.
