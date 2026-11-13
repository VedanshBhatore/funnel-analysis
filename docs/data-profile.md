# Data Profile: GA4 Obfuscated Sample E-commerce Dataset

Source table: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

## Date range

- Min `event_date`: **20201101**
- Max `event_date`: **20210131**
- Number of daily shard tables present: **92**

## Core volume

- Total events: **4,295,584**
- Distinct users (`user_pseudo_id`): **270,154**
- Distinct sessions (`user_pseudo_id` + `ga_session_id`): **360,129**
- Events missing `ga_session_id`: **0** (excluded from all session-level analysis)
- Distinct purchases (`transaction_id` on `purchase` events): **4,452**

## Event name counts

| event_name | count |
|---|---|
| page_view | 1,350,428 |
| user_engagement | 1,058,721 |
| scroll | 493,072 |
| view_item | 386,068 |
| session_start | 354,970 |
| first_visit | 257,462 |
| view_promotion | 190,104 |
| add_to_cart | 58,543 |
| begin_checkout | 38,757 |
| select_item | 31,007 |
| view_search_results | 26,172 |
| add_shipping_info | 19,722 |
| add_payment_info | 13,899 |
| select_promotion | 9,450 |
| purchase | 5,692 |
| click | 1,446 |
| view_item_list | 71 |

## Obfuscation / data-quality quirks observed

### device.category

| device_category | n_events |
|---|---|
| desktop | 2,498,330 |
| mobile | 1,704,069 |
| tablet | 93,185 |

### geo.country (top 15)

| country | n_events |
|---|---|
| United States | 1,910,483 |
| India | 391,859 |
| Canada | 324,261 |
| United Kingdom | 133,383 |
| France | 82,514 |
| Spain | 81,713 |
| China | 76,159 |
| Taiwan | 72,484 |
| Germany | 71,673 |
| Italy | 61,258 |
| Singapore | 56,869 |
| Japan | 56,676 |
| South Korea | 51,584 |
| Netherlands | 50,303 |
| Turkey | 45,168 |

### traffic_source.medium / source (top 15)

| medium | source | n_events |
|---|---|---|
| organic | google | 1,323,449 |
| (none) | (direct) | 989,684 |
| <Other> | <Other> | 597,476 |
| referral | <Other> | 412,242 |
| referral | shop.googlemerchandisestore.com | 365,774 |
| (data deleted) | (data deleted) | 308,624 |
| cpc | google | 176,963 |
| organic | <Other> | 115,950 |
| (data deleted) | <Other> | 5,293 |
| referral | (data deleted) | 71 |
| cpc | <Other> | 52 |
| <Other> | google | 6 |

### items.item_category (top 15, item-row granularity)

| item_category | n_item_rows |
|---|---|
| Home/Apparel/Men's / Unisex/ | 666,832 |
| Home/Sale/ | 543,276 |
| Home/Apparel/ | 225,866 |
| Lifestyle/Drinkware/ | 207,665 |
| Home/Apparel/Women's/ | 202,874 |
| Home/Apparel/Hats/ | 190,073 |
| Home/New/ | 154,949 |
| Lifestyle/Bags/ | 150,352 |
| (not set) | 148,459 |
| Home/Shop by Brand/Google/ | 140,726 |
| Lifestyle/Small Goods/ | 140,697 |
| Home/Shop by Brand/YouTube/ | 137,843 |
| Home/Apparel/Kids/ | 122,614 |
| Home/Eco-Friendly/ | 105,966 |
| Lifestyle/ | 105,650 |

## How obfuscation / quirks are handled in this project

- `<Other>`, `(not set)`, `(data deleted)` and NULL values in dimension columns (device, geo, traffic_source, item_category) are kept as their own explicit category in every GROUP BY (coalesced to a readable label like `(not set)`), never silently filtered out -- dropping them would shrink the denominator and inflate rates computed on the remaining rows.
- Rows with no `ga_session_id` event param are excluded from every **session**-level query (funnel, cohort-by-session, time patterns) because they cannot be assigned to a session; the excluded count is reported above so the exclusion is auditable.
- `purchase` events are de-duplicated by `ecommerce.transaction_id` before computing revenue/orders/AOV, since the same transaction can fire more than one `purchase` event in GA4 (e.g. a confirmation-page reload).
- **`item_id`/`item_category` are not consistent between pre-purchase and purchase events in this sample.** `view_item` and `add_to_cart` agree with each other (416 of 427 distinct viewed `item_id`s also appear on `add_to_cart`), but only 5 of those 427 viewed `item_id`s, and only 15 of 75 view/cart `item_category` values, ever appear on a `purchase` line item (810 distinct purchased `item_id`s exist, in a largely different value space). This looks like an artifact of how Google obfuscated/re-keyed this particular public sample rather than real GA4 behavior. Consequence: `sql/05_product_funnel.sql` reports view-to-cart rate by category/item (consistent taxonomy) and top purchased categories by revenue (purchase events' own, different taxonomy) as **separate** results instead of chaining them into one view→cart→purchase rate per item.
