---
created_at: 2026-07-23T15:53:45.819258+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Changeover tier keys must match plant category, not line type
source: memory_save_learning
---
# Changeover tier keys must match plant category, not line type

The `_CHANGEOVER_MATRICES` dict in `nexusfab/seed/products.py` is keyed by **plant category** (e.g. `"CONFECTIONERY"`, `"PET_FOOD"`) matching `ProductSeed.category`, NOT by line type from the research doc (e.g. "Snack/Confectionery Line", "Dry Powder/Blending Line"). The research doc §5.1 names matrices by line type, but the code looks up via `p1.category` at runtime. If a future task adds a new plant or product category, the matrix key must match the category string in the `PRODUCTS` list, or `get_changeover_info()` falls through to the 60-min default.

Also: `_PRODUCT_TIER` maps every SKU individually (34 entries). When adding new SKUs to `PRODUCTS`, you MUST also add them to `_PRODUCT_TIER` — the self-check `assert len(_PRODUCT_TIER) == 34` will catch a mismatch but only if updated to the new count. The tier string must exist as a key-pair in the matching `_CHANGEOVER_MATRICES[category]` dict or the lookup returns the conservative 60-min/standard fallback silently.
