from typing import Any

from pydantic import BaseModel, ConfigDict


class WorkforceReport(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"plant_id": "PLANT01", "shifts": [], "total_headcount": 48, "labor_cost": 95000.0}},
    )
    plant_id: str | None = None


class AllergenCheckResult(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"from_sku": "SKU001", "to_sku": "SKU002", "requires_cip": True, "cip_class": "CLASS_A", "allergen_conflict": True, "allergens_to_clean": ["GLUTEN"]}},
    )
