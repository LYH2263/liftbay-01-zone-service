# LiftBay

电梯派梯：同向优先与楼层距离评分，轿厢满员拒绝派工；每台轿厢登记可停楼层区间（高/低区），区间外呼梯不派给该轿厢。

## 服务区间（高/低区）

- 每台轿厢有 `min_floor`–`max_floor` 服务区间，在轿厢页维护并持久化（`PATCH /api/cars/{id}`）。
- 评分派工先过区间门：区间外的轿厢直接出局，同向/距离加分只在候选集合内生效；满员拒绝同样只在候选集合内判定。
- 呼梯登记时若本楼没有任何轿厢覆盖该层，直接拒绝登记（409），票据落库为 `rejected` 并写回放说明，不留永远派不出去的 `waiting`。
- 派工页待派列表标注覆盖该层的候选轿厢编号；派工成功后轿厢当前楼层必落在本车区间内。
- 种子数据：A1/A3 只停低区 1–6 层，A2/A4 只停高区 13–18 层，中间层 7–12 呼梯登记即被拒。

## 启动

```bash
docker compose up --build
```

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:4200 |
| API | http://localhost:9200 |
| API 文档 | http://localhost:9200/docs |
| Postgres | localhost:5443 |

健康检查：`GET http://localhost:9200/api/health`

## 页面

- `/buildings` — 楼栋
- `/cars` — 轿厢
- `/calls` — 呼梯
- `/dispatch` — 派工
- `/replay` — 回放
- `/congestion` — 拥堵

## 使用说明

1. 查看楼栋与轿厢状态。
2. 在呼梯页登记请求，在派工页按评分分配轿厢。
3. 回放页查看派工轨迹，拥堵页查看高峰楼层。

## 开发与测试

```bash
docker compose exec api pytest -q
```
