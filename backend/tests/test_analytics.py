import pytest
from fastapi.testclient import TestClient


def test_analytics_endpoints(client: TestClient):
    # 1. Test Overview KPI
    res_overview = client.get("/api/v1/analytics/overview")
    assert res_overview.status_code == 200
    data_overview = res_overview.json()
    assert "total_requests" in data_overview
    assert "pending_requests" in data_overview
    assert "active_missions" in data_overview
    assert "completed_missions" in data_overview
    assert "critical_requests" in data_overview
    assert "total_distributions" in data_overview
    assert "completed_distributions" in data_overview
    assert "total_donations" in data_overview
    assert "low_stock_items" in data_overview

    # 2. Test Priority Distribution
    res_prio = client.get("/api/v1/analytics/priority-distribution")
    assert res_prio.status_code == 200
    prio_data = res_prio.json()
    assert "critical" in prio_data
    assert "high" in prio_data
    assert "medium" in prio_data
    assert "low" in prio_data

    # 3. Test Disaster Types Breakdown
    res_disasters = client.get("/api/v1/analytics/disaster-types")
    assert res_disasters.status_code == 200
    assert isinstance(res_disasters.json(), list)

    # 4. Test Mission Performance
    res_perf = client.get("/api/v1/analytics/mission-performance")
    assert res_perf.status_code == 200
    perf_data = res_perf.json()
    assert "completed_missions" in perf_data
    assert "active_missions" in perf_data
    assert "cancelled_missions" in perf_data
    assert "has_timing_metrics" in perf_data

    # 5. Test Inventory Summary
    res_inv = client.get("/api/v1/analytics/inventory-summary")
    assert res_inv.status_code == 200
    inv_data = res_inv.json()
    assert "total_catalog_items" in inv_data
    assert "available_stock" in inv_data
    assert "reserved_stock" in inv_data
    assert "low_stock_count" in inv_data
