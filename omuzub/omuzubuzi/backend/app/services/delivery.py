"""
MOD-06: Delivery fee calculator and vehicle classifier
"""
from app.models.delivery import VehicleType

def classify_vehicle(weight_kg: float) -> VehicleType:
    """FR-06-01: Classify by weight"""
    if weight_kg < 20:
        return VehicleType.boda
    elif weight_kg <= 200:
        return VehicleType.tuktuk
    else:
        return VehicleType.fuso

BASE_RATES = {
    VehicleType.boda:   {"base": 2000, "per_km": 500},   # UGX
    VehicleType.tuktuk: {"base": 5000, "per_km": 1000},
    VehicleType.fuso:   {"base": 20000, "per_km": 2500},
}

def calculate_delivery_fee(distance_km: float, vehicle_type: VehicleType) -> float:
    """FR-06-06: Delivery fee = base + per_km * distance"""
    rate = BASE_RATES[vehicle_type]
    return round(rate["base"] + rate["per_km"] * distance_km)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line distance in km between two coordinates"""
    import math
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
