from app.services.dispatch_engine import (
    CallRequest,
    CarState,
    covering_car_ids,
    covers_floor,
    pick_car,
    score_car,
)


def test_reject_when_full():
    car = CarState(1, 5, "idle", load=8, capacity=8)
    call = CallRequest(1, 5, "up", passengers=1)
    r = score_car(car, call)
    assert r.accepted is False
    assert "满员" in r.reason


def test_same_direction_beats_far_idle():
    cars = [
        CarState(1, 2, "up", load=1, capacity=10),
        CarState(2, 12, "idle", load=0, capacity=10),
    ]
    call = CallRequest(9, 4, "up", 1)
    best = pick_car(cars, call)
    assert best is not None
    assert best.car_id == 1


def test_closer_idle_wins_when_opposite():
    cars = [
        CarState(1, 10, "down", load=0, capacity=10),
        CarState(2, 3, "idle", load=0, capacity=10),
    ]
    call = CallRequest(3, 2, "up", 1)
    best = pick_car(cars, call)
    assert best is not None
    assert best.car_id == 2


def test_out_of_zone_top_scorer_skipped():
    """区间外的车即使同向/距离裸分最高，也必须被跳过。"""
    low = CarState(1, 3, "idle", load=0, capacity=10, min_floor=1, max_floor=6)
    high = CarState(2, 5, "idle", load=0, capacity=10, min_floor=13, max_floor=18)
    call = CallRequest(1, 5, "up", passengers=1)
    # 高区车正停在 5 层且空闲：若不看区间，距离 0 + 空闲加分必然最高
    r = score_car(high, call)
    assert r.accepted is False
    assert "区间" in r.reason
    best = pick_car([low, high], call)
    assert best is not None
    assert best.car_id == 1


def test_no_coverage_floor_has_no_candidates():
    """本楼无任何轿厢覆盖该层时候选为空，登记侧据此直接拒登。"""
    cars = [
        CarState(1, 3, "up", load=2, capacity=10, min_floor=1, max_floor=6),
        CarState(2, 15, "down", load=4, capacity=10, min_floor=13, max_floor=18),
    ]
    # 中间层 7–12 无覆盖
    assert covering_car_ids(cars, 9) == []
    assert pick_car(cars, CallRequest(2, 9, "up", 1)) is None
    # 低区层候选不含高区车，高区层候选不含低区车
    assert covering_car_ids(cars, 4) == [1]
    assert covering_car_ids(cars, 16) == [2]


def test_full_car_inside_zone_still_rejected():
    """满员拒绝在候选集合（区间内）仍然生效。"""
    car = CarState(1, 4, "idle", load=8, capacity=8, min_floor=1, max_floor=6)
    assert covers_floor(car, 4)
    r = score_car(car, CallRequest(3, 4, "up", 1))
    assert r.accepted is False
    assert "满员" in r.reason
