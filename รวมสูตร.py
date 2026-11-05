import streamlit as st
import os
import math
import pandas as pd
from collections import Counter, defaultdict

st.set_page_config(page_title="HANOI AI PROFESSIONAL v2.0", layout="wide")

CSV_FILE = "history_hanoi.csv"
MIN_HISTORY_FOR_DYNAMIC_WEIGHT = 5
RECENT_WINDOW = 30

DEFAULT_DAILY_NUMBERS = {
    "Monday": "056787",     # เลขประจำวันจันทร์
    "Tuesday": "657872",    # เลขประจำวันอังคาร
    "Wednesday": "390768",  # เลขประจำวันพุธ
    "Thursday": "897693",   # เลขประจำวันพฤหัสบดี
    "Friday": "305687",     # เลขประจำวันศุกร์
    "Saturday": "7890123",  # เลขประจำวันเสาร์
    "Sunday": "8901234"     # เลขประจำวันอาทิตย์
}

FORMULAS = [
    "Carry Over",
    "±1",
    "Sum Modulo",
    "Cross Sum",
    "Daily 6-Digit",
    "Rotation",
    "Mirror",
    "Shift +2",
    "Double",
    "Sandwich",
]

def zfill_num(value, width):
    try:
        if pd.isna(value):
            return "0" * width
        s = str(value).strip()
        if "." in s:
            s = s.split(".")[0]
        return s.zfill(width)[-width:]
    except Exception:
        return "0" * width

def parse_thai_date(x):
    try:
        parts = str(x).strip().split("/")
        if len(parts) != 3:
            return pd.NaT
        day, month, year = map(int, parts)
        if year < 100:
            year += 2500
        if year >= 2400:
            year -= 543
        return pd.Timestamp(year=year, month=month, day=day)
    except Exception:
        return pd.NaT

def initialize_csv():
    if not os.path.exists(CSV_FILE):
        initial_data = [
            ["05/11/2569", "24502", "42500", "502", "00"],
            ["04/11/2569", "53046", "3675", "46", "75"],
            ["03/11/2569", "74446", "97971", "446", "71"],
        ]
        pd.DataFrame(initial_data, columns=[
            "date", "special", "first_prize", "top_3", "bottom_2"
        ]).to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

def load_history():
    if not os.path.exists(CSV_FILE):
        initialize_csv()
    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
    required = ["date", "special", "first_prize", "top_3", "bottom_2"]
    for col in required:
        if col not in df.columns:
            df[col] = ""
    df["dt"] = df["date"].apply(parse_thai_date)
    df = df.dropna(subset=["dt"]).copy()
    df["top_3"] = df["top_3"].apply(lambda x: zfill_num(x, 3))
    df["bottom_2"] = df["bottom_2"].apply(lambda x: zfill_num(x, 2))
    df["weekday_en"] = df["dt"].dt.day_name()
    return df.sort_values("dt", ascending=False).reset_index(drop=True)

def save_history(df):
    out = df.copy()
    for col in ["dt", "weekday_en"]:
        if col in out.columns:
            out = out.drop(columns=[col])
    out.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

def get_transformations(top_3_str, bottom_2_str="00"):
    t3 = zfill_num(top_3_str, 3)
    b2 = zfill_num(bottom_2_str, 2)
    a, b, c = [int(x) for x in t3]
    d, e = [int(x) for x in b2]

    digits = [a, b, c, d, e]
    carry = {str(x) for x in digits}
    pm1 = {str((x + delta) % 10) for x in digits for delta in (-1, 1)}

    sum_t3 = (a + b + c) % 10
    sum_b2 = (d + e) % 10
    sum_total = (sum_t3 + sum_b2) % 10
    sum_formulas = {str(sum_t3), str(sum_b2), str(sum_total)}

    cross_formulas = {
        str((b + e) % 10),
        str((c + d) % 10),
        str((a + d) % 10),
        str((a + e) % 10),
    }

    rotations = {t3[1:] + t3[0], t3[2] + t3[:2]}
    mirror_map = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4}
    mirror = "".join(str(mirror_map[int(x)]) for x in t3)
    shifted = "".join(str((int(x) + 2) % 10) for x in t3)
    doubles = {x * 2 for x in t3}
    sandwiches = {a_str + b_str + a_str for a_str in t3 for b_str in t3 if a_str != b_str}

    return {
        "carry_over": carry,
        "pm1": pm1,
        "sum_formulas": sum_formulas,
        "cross_formulas": cross_formulas,
        "rotations": rotations,
        "mirror": mirror,
        "shifted": shifted,
        "doubles": doubles,
        "sandwiches": sandwiches,
    }

def daily_number_for_day(day, history=None):
    base = DEFAULT_DAILY_NUMBERS.get(day, "000000")
    if history is None or len(history) < MIN_HISTORY_FOR_DYNAMIC_WEIGHT:
        return base
    recent = history.tail(min(RECENT_WINDOW, len(history)))
    freq = Counter()
    for _, row in recent.iterrows():
        freq.update(str(row["top_3"]))
        freq.update(str(row["bottom_2"]))
    score = {str(i): float(freq[str(i)]) for i in range(10)}
    for d in base:
        score[d] += 1.5
    ordered = sorted(score, key=lambda d: (-score[d], d))
    return "".join(ordered[:6])

def formula_candidates(base_t3, base_b2, next_day, history=None):
    trans = get_transformations(base_t3, base_b2)
    daily = daily_number_for_day(next_day, history)
    candidates = defaultdict(set)
    candidates["Carry Over"].update(trans["carry_over"])
    candidates["±1"].update(trans["pm1"])
    candidates["Sum Modulo"].update(trans["sum_formulas"])
    candidates["Cross Sum"].update(trans["cross_formulas"])
    candidates["Daily 6-Digit"].update(daily)
    candidates["Rotation"].update(set("".join(trans["rotations"])))
    candidates["Mirror"].update(trans["mirror"])
    candidates["Shift +2"].update(trans["shifted"])
    candidates["Double"].update(set("".join(trans["doubles"])))
    candidates["Sandwich"].update(set("".join(trans["sandwiches"])))
    return candidates, daily, trans

def evaluate_formula(formula, trans, daily, actual_t3, actual_b2):
    t3 = zfill_num(actual_t3, 3)
    b2 = zfill_num(actual_b2, 2)
    if formula == "Carry Over":
        digits = trans["carry_over"]
        return int(any(d in t3 for d in digits)), int(any(d in b2 for d in digits))
    if formula == "±1":
        digits = trans["pm1"]
        return int(any(d in t3 for d in digits)), int(any(d in b2 for d in digits))
    if formula == "Sum Modulo":
        digits = trans["sum_formulas"]
        return int(any(d in t3 for d in digits)), int(any(d in b2 for d in digits))
    if formula == "Cross Sum":
        digits = trans["cross_formulas"]
        return int(any(d in t3 for d in digits)), int(any(d in b2 for d in digits))
    if formula == "Daily 6-Digit":
        return int(any(d in t3 for d in daily)), int(any(d in b2 for d in daily))
    if formula == "Rotation":
        rots = trans["rotations"]
        return int(any(r == t3 for r in rots)), int(any(set(b2).issubset(set(r)) for r in rots))
    if formula == "Mirror":
        return int(any(d in t3 for d in trans["mirror"])), int(any(d in b2 for d in trans["mirror"]))
    if formula == "Shift +2":
        return int(any(d in t3 for d in trans["shifted"])), int(any(d in b2 for d in trans["shifted"]))
    if formula == "Double":
        return int(any(t3[i] == t3[i + 1] for i in range(2))), int(b2[0] == b2[1])
    if formula == "Sandwich":
        return int(t3[0] == t3[2] or t3[0] == t3[1] or t3[1] == t3[2]), 0
    return 0, 0

def exact_pattern_score(formula, trans, daily, actual_t3, actual_b2):
    t3 = zfill_num(actual_t3, 3)
    b2 = zfill_num(actual_b2, 2)
    if formula == "Rotation":
        if t3 in trans["rotations"]:
            return 1.0, 1.0
    if formula == "Mirror":
        return float(t3 == trans["mirror"]), float(b2 == trans["mirror"][-2:])
    if formula == "Shift +2":
        return float(t3 == trans["shifted"]), float(b2 == trans["shifted"][-2:])
    if formula == "Daily 6-Digit":
        return len(set(t3) & set(daily)) / 3.0, len(set(b2) & set(daily)) / 2.0
    return 0.0, 0.0

def backtest_dataframe(df):
    if len(df) < 2:
        return pd.DataFrame()
    rows = []
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        actual = df.iloc[i]
        day = actual["weekday_en"]
        daily = daily_number_for_day(day, df.iloc[:i])
        trans = get_transformations(prev["top_3"], prev["bottom_2"])
        for formula in FORMULAS:
            hit3, hit2 = evaluate_formula(formula, trans, daily, actual["top_3"], actual["bottom_2"])
            exact3, exact2 = exact_pattern_score(formula, trans, daily, actual["top_3"], actual["bottom_2"])
            rows.append({
                "date": actual["date"],
                "weekday": day,
                "formula": formula,
                "hit_3d": hit3,
                "hit_2d": hit2,
                "exact_3d": exact3,
                "exact_2d": exact2,
            })
    return pd.DataFrame(rows)

def formula_ranking(df):
    bt = backtest_dataframe(df)
    if bt.empty:
        return pd.DataFrame()
    result = []
    for formula in FORMULAS:
        x = bt[bt["formula"] == formula]
        n = len(x)
        if n == 0:
            continue
        hit3 = x["hit_3d"].sum()
        hit2 = x["hit_2d"].sum()
        avg_exact3 = x["exact_3d"].mean()
        avg_exact2 = x["exact_2d"].mean()
        composite = (
            0.40 * (hit3 / n) +
            0.35 * (hit2 / n) +
            0.15 * avg_exact3 +
            0.10 * avg_exact2
        ) * 100
        result.append({
            "Formula": formula,
            "N": n,
            "3D Hit%": round(hit3 / n * 100, 1),
            "2D Hit%": round(hit2 / n * 100, 1),
            "3D Exact%": round(avg_exact3 * 100, 1),
            "2D Exact%": round(avg_exact2 * 100, 1),
            "Composite": round(composite, 1),
        })
    return pd.DataFrame(result).sort_values("Composite", ascending=False).reset_index(drop=True)

def dynamic_weights(df):
    ranking = formula_ranking(df)
    if ranking.empty:
        return {f: 1.0 for f in FORMULAS}
    weights = {}
    for _, row in ranking.iterrows():
        w = 0.5 + row["Composite"] / 50.0
        weights[row["Formula"]] = max(0.5, min(3.0, w))
    return weights

def digit_scores(df, next_day):
    if df.empty:
        return {str(i): 0.0 for i in range(10)}, {}, "000000"
    latest = df.iloc[0]
    candidates, daily, trans = formula_candidates(latest["top_3"], latest["bottom_2"], next_day, df)
    weights = dynamic_weights(df)
    scores = {str(i): 0.0 for i in range(10)}
    for formula in FORMULAS:
        w = weights.get(formula, 1.0)
        for digit in candidates[formula]:
            scores[str(digit)] += w
    recent = df.tail(min(20, len(df)))
    freq = Counter()
    for _, row in recent.iterrows():
        freq.update(row["top_3"])
        freq.update(row["bottom_2"])
    for d, n in freq.items():
        scores[d] += min(1.0, n / max(10, len(recent) * 3))
    return scores, weights, daily

def generate_prediction(df, next_day):
    if df.empty:
        return None
    latest = df.iloc[0]
    scores, weights, daily = digit_scores(df, next_day)
    ordered = sorted(scores, key=lambda d: (-scores[d], d))
    den = ordered[0]
    rong = ordered[1:4]
    kan = ordered[4:7]

    pairs = []
    for r in rong:
        pairs.extend([den + r, r + den])
    pairs = list(dict.fromkeys(pairs))

    top4 = ordered[:4]
    triples = []
    for a in top4:
        for b in top4:
            for c in top4:
                if len({a, b, c}) >= 2:
                    triples.append(a + b + c)
    triples = sorted(set(triples), key=lambda x: -(scores[x[0]] + scores[x[1]] + scores[x[2]]))[:12]

    doubles = [d + d for d in ordered[:4]]
    sandwiches = [a + b + a for a in ordered[:4] for b in ordered[:4] if a != b]
    sandwiches = sandwiches[:8]

    return {
        "latest": latest,
        "daily": daily,
        "scores": scores,
        "ordered": ordered,
        "den": den,
        "rong": rong,
        "kan": kan,
        "pairs": pairs,
        "triples": triples,
        "doubles": doubles,
        "sandwiches": sandwiches,
        "weights": weights,
    }

# --- STREAMLIT UI ---
initialize_csv()
st.title("🇻🇳 HANOI AI PROFESSIONAL v2.0")
st.markdown("ระบบวิเคราะห์และทำนายผลหวยฮานอย ดึงข้อมูลฐานล่าสุดจาก `history_hanoi.csv` อัตโนมัติ")

menu = st.sidebar.selectbox("📌 เลือกเมนูการใช้งาน", [
    "1. ทำนายผลล่วงหน้า (Forward Prediction)",
    "2. อัปเดตผลรางวัล",
    "3. ตรวจสอบประวัติ (History)",
    "4. จัดอันดับสูตร / Backtest",
    "5. เลขประจำวัน (Daily Numbers)"
])

df = load_history()

day_th_map = {
    "Monday": "วันจันทร์",
    "Tuesday": "วันอังคาร",
    "Wednesday": "วันพุธ",
    "Thursday": "วันพฤหัสบดี",
    "Friday": "วันศุกร์",
    "Saturday": "วันเสาร์",
    "Sunday": "วันอาทิตย์"
}

if "1." in menu:
    st.header("🎯 ทำนายผลล่วงหน้า (Forward Prediction)")
    selected_day_th = st.selectbox("เลือกวันสำหรับงวดถัดไป", list(day_th_map.values()))
    next_day = [k for k, v in day_th_map.items() if v == selected_day_th][0]

    if df.empty:
        st.warning("⚠️ ยังไม่มีข้อมูลในระบบ กรุณาเพิ่มข้อมูลงวดก่อนหน้าก่อน")
    else:
        latest = df.iloc[0]
        p = generate_prediction(df, next_day)

        st.info(f"📌 ข้อมูลฐานล่าสุดจาก CSV: งวดวันที่ **{latest['date']}** | 3 ตัวบน: **{latest['top_3']}** | 2 ตัวล่าง: **{latest['bottom_2']}**")
        st.write(f"📅 เลขประจำวัน (Daily 6-Digit) สำหรับ {selected_day_th}: `{p['daily']}`")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="🎯 เลขเด่น (Top Pick)", value=p["den"], delta=f"Score: {p['scores'][p['den']]:.2f}")
        with col2:
            st.metric(label="🥈 เลขรอง", value=" - ".join(p["rong"]))
        with col3:
            st.metric(label="🥉 เลขกัน", value=" - ".join(p["kan"]))

        st.subheader("💡 แนวทางตัวเลขจัดชุด")
        st.markdown(f"**2D เน้นไป-กลับ:** `{', '.join(p['pairs'])}`")
        st.markdown(f"**3D ชุด AI:** `{', '.join(p['triples'][:10])}`")
        st.markdown(f"**เบิ้ล:** `{', '.join(p['doubles'])}`")
        st.markdown(f"**หาม:** `{', '.join(p['sandwiches'])}`")

elif "2." in menu:
    st.header("📝 อัปเดตผลรางวัลหวยฮานอย")
    with st.form("update_form"):
        date_str = st.text_input("ใส่วันที่ (DD/MM/YYYY พ.ศ., เช่น 06/11/2569)")
        special = st.text_input("รางวัลพิเศษ (5 หลัก)")
        first_prize = st.text_input("รางวัลที่ 1 (5 หลัก)")
        top_3 = st.text_input("เลข 3 ตัวบน (3 หลัก)")
        bottom_2 = st.text_input("เลข 2 ตัวล่าง (2 หลัก)")
        submitted = st.form_submit_button("💾 บันทึกผลรางวัล")

        if submitted:
            if not date_str or not top_3 or not bottom_2:
                st.error("⚠️ กรุณากรอกวันที่ 3 ตัวบน และ 2 ตัวล่างให้ครบถ้วน")
            else:
                new_row = pd.DataFrame([{
                    "date": date_str,
                    "special": special,
                    "first_prize": first_prize,
                    "top_3": zfill_num(top_3, 3),
                    "bottom_2": zfill_num(bottom_2, 2),
                }])
                new_row["dt"] = new_row["date"].apply(parse_thai_date)
                new_row["weekday_en"] = new_row["dt"].dt.day_name()

                raw = df.drop(columns=["dt", "weekday_en"], errors="ignore")
                raw = pd.concat([new_row.drop(columns=["dt", "weekday_en"]), raw], ignore_index=True)
                raw = raw.drop_duplicates(subset=["date"], keep="first")
                raw["dt"] = raw["date"].apply(parse_thai_date)
                raw = raw.sort_values("dt", ascending=False)
                save_history(raw)
                st.success("✅ บันทึกผลรางวัลใหม่สำเร็จ! ข้อมูลฐานถูกอัปเดตเรียบร้อย")

elif "3." in menu:
    st.header("📜 ประวัติผลรางวัลทั้งหมด (History)")
    st.write(f"จำนวนข้อมูลทั้งหมด: **{len(df)}** งวด")
    cols = ["date", "special", "first_prize", "top_3", "bottom_2", "weekday_en"]
    st.dataframe(df[cols], use_container_width=True)

elif "4." in menu:
    st.header("📈 การจัดอันดับสูตร / Backtest")
    df_sorted = df.sort_values("dt").reset_index(drop=True)
    if len(df_sorted) < 2:
        st.warning("⚠️ ข้อมูลไม่เพียงพอ ต้องมีอย่างน้อย 2 งวด")
    else:
        ranking = formula_ranking(df_sorted)
        st.dataframe(ranking, use_container_width=True)

elif "5." in menu:
    st.header("📅 เลขประจำวัน (Daily Numbers)")
    df_sorted = df.sort_values("dt").reset_index(drop=True)
    daily_data = []
    for en, th in day_th_map.items():
        daily_data.append({"วัน": th, "Daily 6-Digit": daily_number_for_day(en, df_sorted)})
    st.dataframe(pd.DataFrame(daily_data), use_container_width=True)
