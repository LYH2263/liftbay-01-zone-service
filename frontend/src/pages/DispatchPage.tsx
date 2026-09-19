import { useEffect, useState } from "react";
import { api } from "../api/client";
type Call = { id: number; floor: number; direction: string; passengers: number; status: string; score: string; assigned_car_id: number | null };
type Car = { id: number; label: string; min_floor: number; max_floor: number };
export default function DispatchPage() {
  const [rows, setRows] = useState<Call[]>([]);
  const [cars, setCars] = useState<Car[]>([]);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  const reload = () => api<Call[]>("/calls").then(setRows);
  useEffect(() => { reload(); api<Car[]>("/cars").then(setCars); }, []);
  async function run(id: number) {
    setMsg(""); setErr("");
    try {
      const c = await api<Call>("/dispatch", { method: "POST", body: JSON.stringify({ call_id: id }) });
      setMsg(`呼梯 #${c.id} → 轿厢 ${c.assigned_car_id}，评分 ${c.score}`);
      reload();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); reload(); }
  }
  const waiting = rows.filter(r => r.status === "waiting");
  const candidates = (floor: number) => cars.filter(c => c.min_floor <= floor && floor <= c.max_floor);
  return (<>
    <h2>派工</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>呼梯</th><th>楼层</th><th>方向</th><th>人数</th><th>候选轿厢</th><th></th></tr></thead>
    <tbody>{waiting.map(c => {
      const cands = candidates(c.floor);
      return <tr key={c.id}><td>#{c.id}</td><td>{c.floor}</td><td>{c.direction}</td><td>{c.passengers}</td>
        <td className="mono">{cands.length ? cands.map(car => `${car.label}(#${car.id})`).join(" ") : "无覆盖"}</td>
        <td><button onClick={() => run(c.id)}>评分派轿厢</button></td></tr>;
    })}
      {!waiting.length && <tr><td colSpan={6}>暂无待派呼梯</td></tr>}
    </tbody></table>
  </>);
}
