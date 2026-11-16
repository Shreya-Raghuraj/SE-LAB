
import pytest
from shipping_quote import process_shipments, monitor_container_pressures


# 1. Invalid shipment input
def test_invalid_shipments():
    with pytest.raises(ValueError):
        process_shipments("not a list", 10.0)


# 2. Negative handling fee
def test_negative_handling_fee():
    with pytest.raises(ValueError):
        process_shipments([], -5.0)


# 3. Ground shipment with different package conditions
def test_ground_shipment_all_package_types():
    shipments = [
        {
            "manifest_approved": False,
            "packages": []
        },
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": False,
            "express_priority": True,
            "packages": [
                {"weight_kg": 0, "is_hazmat": False},
                {"weight_kg": 1, "is_hazmat": True},
                {"weight_kg": 40, "is_hazmat": False},
                {"weight_kg": 10, "is_hazmat": False}
            ]
        }
    ]

    result = process_shipments(shipments, 20.0)
    assert result["total_quote"] == 437.5
    assert result["status"] == "CLEARED"


# 4. Air shipment
def test_air_shipment():
    shipments = [{
        "manifest_approved": True,
        "mode": "air",
        "packages": [
            {"weight_kg": 2, "is_hazmat": False}
        ]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 34.0
    assert result["status"] == "CLEARED"


# 5. Unsupported transport mode
def test_unsupported_transport_mode():
    shipments = [{
        "manifest_approved": True,
        "mode": "sea",
        "packages": [
            {"weight_kg": 5}
        ]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


# 6. Fragile shipment containing hazardous material
def test_fragile_hazmat_shipment():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "is_fragile": True,
        "packages": [
            {"weight_kg": 5, "is_hazmat": True}
        ]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


# 7. More than three rejected parcels
def test_flagged_review():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [
            {"weight_kg": 0},
            {"weight_kg": -1},
            {"weight_kg": 0},
            {"weight_kg": -5}
        ]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["status"] == "FLAGGED_REVIEW"


# 8. Empty shipment list
def test_no_cargo():
    result = process_shipments([], 10.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


# 9. Empty pressure logs
def test_pressure_no_data():
    assert monitor_container_pressures([]) == "NO_DATA"


# 10. Stable container pressure
def test_pressure_stable():
    assert monitor_container_pressures(
        [[15.0, 16.0, 14.5]]
    ) == "STABLE"


# 11. Leak detected after two consecutive low readings
def test_pressure_leak():
    assert monitor_container_pressures(
        [[15.0, 13.0, 12.0]]
    ) == "LEAK_DETECTED"
