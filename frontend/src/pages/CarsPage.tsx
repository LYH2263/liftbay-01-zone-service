import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
type Car = { id: number; label: string; floor: number; direction: string; load: number; capacity: number; min_floor: number; max_floor: number };
type Call = { id: number; floor: number; status: string };
type B = { floors: number };
type RangeDraft = { min_floor: number; max_floor: number };
export default function CarsPage() {
  const [cars, setCars] = useState<Car[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [floors, setFloors] = useState(18);
  const [drafts, setDrafts] = useState<Record<number, RangeDraft>>({});
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  const reload = () => api<Car[]>("/cars").then(cs => {
    setCars(cs);
    setDrafts(Object.fromEntries(cs.map(c => [c.id, { min_floor: c.min_floor, max_floor: c.max_floor }])));
  });
  useEffect(() => {
    reload();
    api<Call[]>("/calls").then(setCalls);
    api<B[]>("/buildings").then(bs => { if (bs[0]) setFloors(bs[0].floors); });
  }, []);
  const callFloors = useMemo(() => new Set(calls.filter(c => c.status === "waiting").map(c => c.floor)), [calls]);
  const levels = useMemo(() => Array.from({ length: floors }, (_, i) => i + 1), [floors]);
  function setDraft(id: number, patch: Partial<RangeDraft>) {
    setDrafts(d => ({ ...d, [id]: { ...d[id], ...patch } }));
  }
  async function save(car: Car) {
    setMsg(""); setErr("");
    try {
      const d = drafts[car.id];
      await api(`/cars/${car.id}`, { method: "PATCH", body: JSON.stringify(d) });
      setMsg(`轿厢 ${car.label} 服务区间已保存：${d.min_floor}–${d.max_floor} 层`);
      reload();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>轿厢井道</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <div className="shaft-wrap">
      {cars.map(car => (
        <div className="shaft" key={car.id}>
          <h3>{car.label} · {car.load}/{car.capacity} · {car.min_floor}-{car.max_floor}F</h3>
          {levels.map(f => (
            <div key={f} className={`floor-slot ${car.floor === f ? "has-car" : ""} ${callFloors.has(f) ? "has-call" : ""} ${f < car.min_floor || f > car.max_floor ? "out-of-zone" : ""}`}>
              {car.floor === f ? car.direction : f}
            </div>
          ))}
        </div>
      ))}
    </div>
    <h2>服务区间</h2>
    <table className="table"><thead><tr><th>轿厢</th><th>当前楼层</th><th>下限</th><th>上限</th><th></th></tr></thead>
    <tbody>{cars.map(car => {
      const d = drafts[car.id] ?? { min_floor: car.min_floor, max_floor: car.max_floor };
      const inZone = car.floor >= car.min_floor && car.floor <= car.max_floor;
      return <tr key={car.id}>
        <td>{car.label} (#{car.id})</td>
        <td className="mono">{car.floor}F {inZone ? "" : "· 区间外!"}</td>
        <td><input type="number" min={1} max={floors} value={d.min_floor} style={{ width: 72 }}
          onChange={e => setDraft(car.id, { min_floor: Number(e.target.value) })} /></td>
        <td><input type="number" min={1} max={floors} value={d.max_floor} style={{ width: 72 }}
          onChange={e => setDraft(car.id, { max_floor: Number(e.target.value) })} /></td>
        <td><button onClick={() => save(car)}>保存区间</button></td>
      </tr>;
    })}</tbody></table>
  </>);
}
