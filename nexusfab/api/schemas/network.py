from typing import Any

from pydantic import BaseModel, ConfigDict


class NetworkAnalysis(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"network_oee": 0.782, "total_capacity_tons": 5000.0, "plants": [], "transfers": [], "flow_graph": {}}},
    )


class NetworkFlowEntry(BaseModel):
    route: str
    from_plant: str
    to_plant: str
    volume_tons: float
    cost_usd: float
    transit_hours: float
    cold_chain: bool
    cost_per_pallet: float
    active: bool


class NetworkFlow(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"flows": [{"route": "PLANT01→PLANT02", "from_plant": "PLANT01", "to_plant": "PLANT02", "volume_tons": 120.0, "cost_usd": 14400.0, "transit_hours": 6, "cold_chain": True, "cost_per_pallet": 245.0, "active": True}], "total_monthly_cost_usd": 62400.0, "active_routes": 3}},
    )
    flows: list[NetworkFlowEntry]
    total_monthly_cost_usd: float
    active_routes: int


class AllocationPlan(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"products": [], "plants": ["PLANT01", "PLANT02"], "allocation": {}, "plant_summary": {}}},
    )
    products: list[Any]
    plants: list[str]
    allocation: dict[str, Any]
    plant_summary: dict[str, Any]


class TransportCost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"from_plant": "PLANT01", "to_plant": "PLANT02", "cost_per_pallet": 245.0, "lead_time_hours": 6, "cold_chain": True, "distance_km": 180}},
    )
