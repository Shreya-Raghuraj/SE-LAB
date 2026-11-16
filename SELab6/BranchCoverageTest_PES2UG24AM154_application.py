
import pytest
from shipping_quote import process_shipments, monitor_container_pressures


# 1. Invalid shipment input
def test_invalid_shipment_type():
    with pytest.raises(ValueError):
        process_shipments("invalid", 10.0)


# 2. Negative handling fee
def test_negative_handling_fee():
    with pytest.raises(ValueError):
        process_shipments([], -5.0)


# 3. Empty shipment list
def test_empty_shipments():
    result = process_shipments([], 10.0)
    assert result["status"] == "NO_CARGO"


# 4. Unapproved shipment is skipped
def test_unapproved_shipment():
    shipments = [{
        "manifest_approved": False,
        "mode": "ground",
        "packages": [{"weight_kg": 10}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["status"] == "NO_CARGO"


# 5. Ground mode using default transport mode
def test_default_ground_mode():
    shipments = [{
        "manifest_approved": True,
        "packages": [{"weight_kg": 5}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 30.0
    assert result["status"] == "CLEARED"


# 6. Air transport mode
def test_air_mode():
    shipments = [{
        "manifest_approved": True,
        "mode": "air",
        "packages": [{"weight_kg": 2}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 34.0


# 7. Unsupported transport mode
def test_invalid_transport_mode():
    shipments = [{
        "manifest_approved": True,
        "mode": "sea",
        "packages": [{"weight_kg": 5}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["status"] == "NO_CARGO"


# 8. Invalid package weight
def test_invalid_weight():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [{"weight_kg": 0}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["status"] == "CLEARED"


# 9. Normal non-hazardous package
def test_normal_package():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [{"weight_kg": 10, "is_hazmat": False}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 50.0


# 10. Overweight package
def test_overweight_package():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [{"weight_kg": 40, "is_hazmat": False}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 250.0


# 11. Non-fragile hazardous package
def test_non_fragile_hazmat():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "is_fragile": False,
        "packages": [{"weight_kg": 5, "is_hazmat": True}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 60.0


# 12. Fragile hazardous package
def test_fragile_hazmat():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "is_fragile": True,
        "packages": [{"weight_kg": 5, "is_hazmat": True}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 0.0
    assert result["status"] == "NO_CARGO"


# 13. Express priority enabled
def test_express_priority():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "express_priority": True,
        "packages": [{"weight_kg": 10}]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["total_quote"] == 62.5


# 14. More than three rejected parcels
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


# 15. Three or fewer rejected parcels
def test_cleared_with_rejected_parcel():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [
            {"weight_kg": 0},
            {"weight_kg": 5}
        ]
    }]

    result = process_shipments(shipments, 10.0)
    assert result["status"] == "CLEARED"


# 16. Empty packages
def test_empty_packages():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": []
    }]

    result = process_shipments(shipments, 10.0)
    assert result["status"] == "CLEARED"


# 17. No pressure logs
def test_no_pressure_logs():
    assert monitor_container_pressures([]) == "NO_DATA"


# 18. Empty container pressure readings
def test_empty_container_readings():
    assert monitor_container_pressures([[]]) == "STABLE"


# 19. Stable pressure readings
def test_stable_pressure():
    assert monitor_container_pressures(
        [[15.0, 16.0, 17.0]]
    ) == "STABLE"


# 20. One low reading followed by normal pressure
def test_pressure_streak_reset():
    assert monitor_container_pressures(
        [[13.0, 15.0, 16.0]]
    ) == "STABLE"


# 21. Two consecutive low readings
def test_leak_detected():
    assert monitor_container_pressures(
        [[15.0, 13.0, 12.0]]
    ) == "LEAK_DETECTED"
