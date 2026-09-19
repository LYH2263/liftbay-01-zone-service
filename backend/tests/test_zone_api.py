"""API 级测例：服务区间在登记、派工、轿厢区间维护上的端到端行为。

用 SQLite 内存库替换 Postgres，只挂 api_router，不触发 main 的 lifespan/种子。
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.router import api_router
from app.database import Base, get_db
from app.models.models import Building, ElevatorCar


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(api_router, prefix="/api")
    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    b = Building(name="测试楼", floors=18)
    db.add(b)
    db.flush()
    db.add_all(
        [
            # 低区车：只停 1–6 层
            ElevatorCar(building_id=b.id, label="L1", floor=2, direction="idle", load=0, capacity=10, min_floor=1, max_floor=6),
            # 高区车：只停 13–18 层
            ElevatorCar(building_id=b.id, label="H1", floor=15, direction="idle", load=0, capacity=10, min_floor=13, max_floor=18),
        ]
    )
    db.commit()
    building_id = b.id
    db.close()

    with TestClient(app) as c:
        yield c, building_id


def test_register_call_without_coverage_rejected(client):
    api, building_id = client
    r = api.post(
        "/api/calls",
        json={"building_id": building_id, "floor": 9, "direction": "up", "passengers": 1},
    )
    assert r.status_code == 409
    # 不留 waiting：该呼梯以 rejected 落库
    calls = api.get("/api/calls").json()
    ticket = next(c for c in calls if c["floor"] == 9)
    assert ticket["status"] == "rejected"
    # 回放有拒绝说明
    logs = api.get("/api/replay").json()
    assert any(
        log["call_id"] == ticket["id"] and "无轿厢覆盖" in log["detail"] for log in logs
    )


def test_low_zone_call_dispatched_to_low_car_only(client):
    api, building_id = client
    r = api.post(
        "/api/calls",
        json={"building_id": building_id, "floor": 4, "direction": "up", "passengers": 1},
    )
    assert r.status_code == 200
    call_id = r.json()["id"]
    r = api.post("/api/dispatch", json={"call_id": call_id})
    assert r.status_code == 200
    cars = {c["label"]: c for c in api.get("/api/cars").json()}
    assert r.json()["assigned_car_id"] == cars["L1"]["id"]
    # 派工成功后轿厢当前楼层仍落在本车区间内
    low = cars["L1"]
    assert low["floor"] == 4
    assert low["min_floor"] <= low["floor"] <= low["max_floor"]


def test_car_range_update_persists(client):
    api, _building_id = client
    car_id = api.get("/api/cars").json()[0]["id"]
    r = api.patch(f"/api/cars/{car_id}", json={"min_floor": 2, "max_floor": 5})
    assert r.status_code == 200
    again = {c["id"]: c for c in api.get("/api/cars").json()}
    assert again[car_id]["min_floor"] == 2
    assert again[car_id]["max_floor"] == 5


def test_car_range_update_validates_bounds(client):
    api, _building_id = client
    car_id = api.get("/api/cars").json()[0]["id"]
    r = api.patch(f"/api/cars/{car_id}", json={"min_floor": 5, "max_floor": 2})
    assert r.status_code == 400
    r = api.patch(f"/api/cars/{car_id}", json={"min_floor": 1, "max_floor": 99})
    assert r.status_code == 400
