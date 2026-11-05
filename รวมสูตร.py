# app.py - Hanoi AI Professional (All-in-One Streamlit App - Multi-CSV & 3-Way Fusion)
import os
import streamlit as st
import pandas as pd

# ==================== ตั้งค่าหน้าเว็บ ====================
st.set_page_config(page_title="Hanoi AI Professional", page_icon="🎯", layout="wide")

# ==================== ชื่อไฟล์ฐานข้อมูลหลักและรายวัน ====================
CSV_FILE = "history_hanoi.csv"

DAY_MAP = {
    "Monday": "mon",
    "Tuesday": "tue",
    "Wednesday": "wed",
    "Thursday": "thu",
    "Friday": "fri",
    "Saturday": "sat",
    "Sunday": "sun",
}

# ==================== ชุดเลขประจำวัน 6 ตัวตามสถิติ ====================
DAILY_NUMBERS = {
    "Monday": "940627",
    "Tuesday": "017562",
    "Wednesday": "394517",
    "Thursday": "643951",
    "Friday": "974516",
    "Saturday": "820739",
    "Sunday": "470076",
}

def parse_thai_date(x):
    """ฟังก์ชันแปลงวันที่พุทธศักราช (DD/MM/YYYY) เป็น ค.ศ. แบบปลอดภัย"""
    try:
        parts = str(x).strip().split("/")
        if len(parts) != 3:
            return pd.NaT
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        if year > 2400:
            year -= 543
        elif year < 100:
            year += 2000
        return pd.Timestamp(year=year, month=month, day=day)
    except Exception:
        return pd.NaT

def clean_dataframe(df):
    """ทำความสะอาดชื่อคอลัมน์รองรับทั้งภาษาอังกฤษและภาษาไทย"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "special", "first_prize", "top_3", "bottom_2"])
    df.columns = df.columns.str.strip()
    column_mapping = {
        "วันที่": "date",
        "รางวัลพิเศษ": "special",
        "รางวัลที่ 1": "first_prize",
        "รางวัลที่ 2": "first_prize",
        "3 ตัวบน": "top_3",
        "3ตัวบน": "top_3",
        "2 ตัวล่าง": "bottom_2",
        "2ตัวล่าง": "bottom_2"
    }
    df = df.rename(columns=column_mapping)
    return df

def load_all_history():
    """โหลดและรวมข้อมูลประวัติจากทุกไฟล์ CSV (ทั้งไฟล์หลักและไฟล์แยกรายวัน)"""
    dfs = []

    # 1. อ่านไฟล์หลัก history_hanoi.csv ถ้ามี
    if os.path.exists(CSV_FILE):
        try:
            df_main_file = pd.read_csv(CSV_FILE)
            dfs.append(clean_dataframe(df_main_file))
        except Exception:
            pass

    # 2. อ่านไฟล์แยกตามวัน เช่น history_hanoi_mon.csv
    for day_en, day_code in DAY_MAP.items():
        daily_filename = f"history_hanoi_{day_code}.csv"
        if os.path.exists(daily_filename):
            try:
                df_daily = pd.read_csv(daily_filename)
                dfs.append(clean_dataframe(df_daily))
            except Exception:
                pass

    if dfs:
        df_combined = pd.concat(dfs, ignore_index=True)
        df_combined = df_combined.dropna(subset=["date"])
        # ลบแถวที่ซ้ำซ้อนตาม วันที่
        df_combined = df_combined.drop_duplicates(subset=["date"]).reset_index(drop=True)
        return df_combined
    else:
        return pd.DataFrame(columns=["date", "special", "first_prize", "top_3", "bottom_2"])

def load_specific_day_history(day_en):
    """โหลดข้อมูลเฉพาะไฟล์ CSV ประจำวันนั้นๆ"""
    day_code = DAY_MAP.get(day_en, "mon")
    filename = f"history_hanoi_{day_code}.csv"
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            return clean_dataframe(df)
        except Exception:
            pass
    return pd.DataFrame(columns=["date", "special", "first_prize", "top_3", "bottom_2"])

def initialize_csv():
    """ตรวจสอบไฟล์ CSV หากยังไม่มีไฟล์ใดๆ ให้สร้างโครงสร้างเริ่มต้น"""
    has_any_file = os.path.exists(CSV_FILE) or any(
        os.path.exists(f"history_hanoi_{code}.csv") for code in DAY_MAP.values()
    )

    if not has_any_file:
        initial_data = """date,special,first_prize,top_3,bottom_2
30/09/2569,95242,82585,242,85
29/09/2569,05651,08389,651,89
28/09/2569,77115,86908,115,08"""
        with open(CSV_FILE, "w", encoding="utf-8") as f:
            f.write(initial_data)

def get_transformations(top_3_str, bottom_2_str="00"):
    """แปลงเลขฐานและสูตรคำนวณทั้งหมด"""
    try:
        clean_t3 = str(top_3_str).split(".")[0].strip().zfill(3)
        clean_b2 = str(bottom_2_str).split(".")[0].strip().zfill(2)
    except Exception:
        clean_t3, clean_b2 = "000", "00"

    digits_t3 = [int(c) for c in clean_t3[-3:]]
    digits_b2 = [int(c) for c in clean_b2[-2:]]

    carry_over = set(digits_t3 + digits_b2)

    pm1 = set()
    for dig in digits_t3 + digits_b2:
        pm1.add((dig + 1) % 10)
        pm1.add((dig - 1) % 10)

    sum_t3 = sum(digits_t3) % 10
    sum_b2 = sum(digits_b2) % 10
    sum_total = (sum_t3 + sum_b2) % 10
    sum_formulas = {str(sum_t3), str(sum_b2), str(sum_total)}

    cross_sum_1 = (digits_t3[1] + digits_b2[1]) % 10
    cross_sum_2 = (digits_t3[2] + digits_b2[0]) % 10
    cross_formulas = {str(cross_sum_1), str(cross_sum_2)}

    rotations = {
        f"{digits_t3[1]}{digits_t3[2]}{digits_t3[0]}",
        f"{digits_t3[2]}{digits_t3[0]}{digits_t3[1]}",
    }
    mirror_map = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4}
    mirrored = "".join([str(mirror_map[d]) for d in digits_t3])
    shifted = "".join([str((d + 2) % 10) for d in digits_t3])

    doubles = {f"{d}{d}" for d in digits_t3}
    sandwiches = {
        f"{d1}{d2}{d1}" for d1 in digits_t3 for d2 in digits_t3 if d1 != d2
    }

    return {
        "carry_over": carry_over,
        "pm1": pm1,
        "sum_formulas": sum_formulas,
        "cross_formulas": cross_formulas,
        "rotations": rotations,
        "mirror": mirrored,
        "shifted": shifted,
        "doubles": doubles,
        "sandwiches": sandwiches,
    }


# ==================== ส่วนแสดงผลหน้าเว็บ Streamlit ====================

initialize_csv()

st.title("🎯 Hanoi AI Professional - ระบบวิเคราะห์หวยฮานอย (3-Way Fusion)")
st.write("ระบบวิเคราะห์สถิติและทำนายแนวทางหวยฮานอยด้วย Python และ Streamlit")

# เมนูด้านข้าง (Sidebar)
menu = st.sidebar.selectbox(
    "เลือกเมนูการใช้งาน",
    [
        "1. อัปเดตผลรางวัล",
        "2. แสดงประวัติ (History)",
        "3. ลบข้อมืองวดล่าสุด",
        "4. Formula Ranking (จัดอันดับสูตร)",
        "5. Forward Prediction (ทำนายงวดถัดไป)",
    ],
)

# โหลดข้อมูล CSV (รวมไฟล์หลัก + ไฟล์รายวัน)
df_main = load_all_history()

# เมนูที่ 1: อัปเดตผลรางวัล
if menu == "1. อัปเดตผลรางวัล":
    st.header("📝 อัปเดตผลรางวัลหวยฮานอยใหม่")

    with st.form("update_form"):
        date_str = st.text_input("ใส่วันที่ (DD/MM/YYYY เช่น 06/10/2569)")
        special = st.text_input("รางวัลพิเศษ (5 หลัก)")
        first_prize = st.text_input("รางวัลที่ 1 (5 หลัก)")
        top_3 = st.text_input("เลข 3 ตัวบน (3 หลัก)")
        bottom_2 = st.text_input("เลข 2 ตัวล่าง (2 หลัก)")

        submitted = st.form_submit_button("บันทึกผลรางวัล")
        if submitted:
            if date_str and top_3 and bottom_2:
                dt_obj = parse_thai_date(date_str)
                if pd.notna(dt_obj):
                    day_en = dt_obj.day_name()
                    day_code = DAY_MAP.get(day_en, "mon")
                    daily_filename = f"history_hanoi_{day_code}.csv"

                    new_row = pd.DataFrame([{
                        "date": date_str,
                        "special": special,
                        "first_prize": first_prize,
                        "top_3": top_3,
                        "bottom_2": bottom_2,
                    }])

                    # 1. บันทึกลงไฟล์หลัก history_hanoi.csv
                    updated_main = pd.concat([new_row, df_main], ignore_index=True)
                    updated_main = updated_main.drop_duplicates(subset=["date"]).reset_index(drop=True)
                    updated_main.to_csv(CSV_FILE, index=False)

                    # 2. บันทึกลงไฟล์แยกรายวัน (เช่น history_hanoi_thu.csv)
                    df_day_existing = load_specific_day_history(day_en)
                    updated_day = pd.concat([new_row, df_day_existing], ignore_index=True)
                    updated_day = updated_day.drop_duplicates(subset=["date"]).reset_index(drop=True)
                    updated_day.to_csv(daily_filename, index=False)

                    st.success(f"✅ บันทึกผลรางวัลลงในไฟล์หลักและไฟล์ประจำวัน **{day_en}** (`{daily_filename}`) เรียบร้อยแล้ว!")
                    st.rerun()
                else:
                    st.warning("⚠️ รูปแบบวันที่ไม่ถูกต้อง กรุณาใส่ในรูปแบบ DD/MM/YYYY")
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลวันที่ 3 ตัวบน และ 2 ตัวล่างให้ครบถ้วน")

# เมนูที่ 2: แสดงประวัติทั้งหมด
elif menu == "2. แสดงประวัติ (History)":
    st.header("📊 ประวัติผลรางวัลหวยฮานอยย้อนหลังทั้งหมด")
    if not df_main.empty:
        st.dataframe(df_main, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# เมนูที่ 3: ลบข้อมืองวดล่าสุด
elif menu == "3. ลบข้อมืองวดล่าสุด":
    st.header("🗑️ ลบข้อมูลผลรางวัล (งวดล่าสุด)")
    if not df_main.empty:
        st.write("ข้อมืองวดล่าสุดด้านบนสุดที่จะถูกลบ:")
        st.dataframe(df_main.head(1), use_container_width=True)

        if st.button("ยืนยันการลบงวดล่าสุด"):
            if len(df_main) > 0:
                df_main = df_main.iloc[1:].reset_index(drop=True)
                df_main.to_csv(CSV_FILE, index=False)
                st.success("✅ ลบงวดล่าสุดเรียบร้อยแล้ว")
                st.rerun()
    else:
        st.info("ไม่มีข้อมูลให้ลบ")

# เมนูที่ 4: จัดอันดับสูตร
elif menu == "4. Formula Ranking (จัดอันดับสูตร)":
    st.header("🏆 จัดอันดับความแม่นยำของสูตร (Formula Ranking)")

    if st.button("เริ่มคำนวณสถิติย้อนหลัง"):
        with st.spinner("กำลังประมวลผล Backtest..."):
            df = df_main.copy()
            df["dt"] = df["date"].apply(parse_thai_date)
            df = (
                df.dropna(subset=["dt"])
                .sort_values(by="dt", ascending=True)
                .reset_index(drop=True)
            )
            df["weekday_en"] = df["dt"].dt.day_name()

            total = len(df) - 1
            if total <= 0:
                st.warning("⚠️ ข้อมูลไม่เพียงพอสำหรับการคำนวณย้อนหลัง")
            else:
                scores = {
                    "Carry Over (ดึงเลขเก่า)": 0,
                    "±1 (วิ่ง/รูด)": 0,
                    "Sum Modulo (ผลรวม)": 0,
                    "Cross Sum (สูตรไขว้)": 0,
                    "Daily 6-Digit": 0,
                    "Rotation (โต๊ด)": 0,
                    "Mirror (กระจก)": 0,
                    "Shift (+2)": 0,
                    "Double (เบิ้ล)": 0,
                    "Sandwich (หาม)": 0,
                }

                for i in range(1, len(df)):
                    prev = df.iloc[i - 1]
                    row = df.iloc[i]
                    t3 = str(row["top_3"]).zfill(3)
                    b2 = str(row["bottom_2"]).zfill(2)
                    base_t3 = str(prev["top_3"]).zfill(3)
                    base_b2 = str(prev["bottom_2"]).zfill(2)
                    daily_6 = DAILY_NUMBERS.get(row["weekday_en"], "000000")

                    trans = get_transformations(base_t3, base_b2)

                    if any(str(d) in t3 or str(d) in b2 for d in trans["carry_over"]):
                        scores["Carry Over (ดึงเลขเก่า)"] += 1
                    if any(str(d) in t3 or str(d) in b2 for d in trans["pm1"]):
                        scores["±1 (วิ่ง/รูด)"] += 1
                    if any(str(d) in t3 or str(d) in b2 for d in trans["sum_formulas"]):
                        scores["Sum Modulo (ผลรวม)"] += 1
                    if any(str(d) in t3 or str(d) in b2 for d in trans["cross_formulas"]):
                        scores["Cross Sum (สูตรไขว้)"] += 1
                    if any(c in t3 or c in b2 for c in daily_6):
                        scores["Daily 6-Digit"] += 1
                    if any(rot in t3 for rot in trans["rotations"]) or any(
                        any(c in b2 for c in rot) for rot in trans["rotations"]
                    ):
                        scores["Rotation (โต๊ด)"] += 1
                    if any(c in t3 or c in b2 for c in trans["mirror"]):
                        scores["Mirror (กระจก)"] += 1
                    if any(c in t3 or c in b2 for c in trans["shifted"]):
                        scores["Shift (+2)"] += 1
                    if any(dbl in t3 or dbl in b2 for dbl in trans["doubles"]):
                        scores["Double (เบิ้ล)"] += 1
                    if any(snd in t3 for snd in trans["sandwiches"]):
                        scores["Sandwich (หาม)"] += 1

                ranked = sorted(
                    scores.items(), key=lambda x: x[1], reverse=True
                )

                result_data = []
                for rank, (formula, score) in enumerate(ranked, 1):
                    percentage = (score / total) * 100
                    result_data.append(
                        {
                            "อันดับ": rank,
                            "ชื่อสูตร": formula,
                            "คะแนนที่ถูก": f"{score}/{total}",
                            "ความแม่นยำ (%)": f"{percentage:.1f}%",
                        }
                    )

                st.table(pd.DataFrame(result_data))

# เมนูที่ 5: ทำนายงวดถัดไป (ระบบผสาน 3 ส่วน: history_hanoi.csv + history_hanoi_{day}.csv + เลขประจำวัน)
elif menu == "5. Forward Prediction (ทำนายงวดถัดไป)":
    st.header("🔮 Forward Prediction (คำนวณผสาน 3 แหล่งข้อมูล)")

    if not df_main.empty:
        day_selected = st.selectbox(
            "เลือกวันของงวดถัดไป",
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
        )

        # 1. ข้อมืองวดรวมล่าสุดจาก history_hanoi.csv
        latest_all = df_main.iloc[0]

        # 2. ข้อมืองวดล่าสุดเฉพาะของวันนั้นๆ (เช่น history_hanoi_thu.csv)
        df_day_specific = load_specific_day_history(day_selected)
        latest_day = df_day_specific.iloc[0] if not df_day_specific.empty else latest_all

        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"📊 **งวดรวมล่าสุด (`history_hanoi.csv`)**\n\nวันที่: **{latest_all.get('date', '-')}**\n\n3 ตัวบน: `{latest_all.get('top_3', '-')}` | 2 ตัวล่าง: `{latest_all.get('bottom_2', '-')}`")
        with col_b:
            st.success(f"📌 **งวดประจำวัน {day_selected} ล่าสุด**\n\nวันที่: **{latest_day.get('date', '-')}**\n\n3 ตัวบน: `{latest_day.get('top_3', '-')}` | 2 ตัวล่าง: `{latest_day.get('bottom_2', '-')}`")

        # 3. เลขประจำวัน 6 ตัวตามสถิติ
        daily_6 = DAILY_NUMBERS.get(day_selected, "000000")
        st.write(f"🎯 **ชุดเลขประจำวัน ({day_selected}):** `{daily_6}`")

        if st.button("🚀 ประมวลผลทำนายเลข (ผสาน 3 ส่วน)"):
            if day_selected == "Saturday":
                st.warning("⚠️ [AI WARNING] วันเสาร์มีสถิติการออก 'เลขเบิ้ล' และ 'เลขหาม' สูงมาก แนะนำให้ติดชุดกันไว้เสมอ!")

            # แปลงสูตรจากงวดรวมล่าสุด
            trans_all = get_transformations(latest_all.get('top_3', '000'), latest_all.get('bottom_2', '00'))
            # แปลงสูตรจากงวดประจำวันล่าสุด
            trans_day = get_transformations(latest_day.get('top_3', '000'), latest_day.get('bottom_2', '00'))

            digit_scores = {str(i): 0.0 for i in range(10)}

            # --- น้ำหนักส่วนที่ 1: เลขประจำวัน 6 ตัว (+2.0 แต้ม) ---
            for d in daily_6:
                digit_scores[d] += 2.0

            # --- น้ำหนักส่วนที่ 2: จากผลรวมล่าสุด (+1.5 แต้ม) ---
            for d in trans_all['carry_over']: digit_scores[str(d)] += 1.5
            for d in trans_all['pm1']: digit_scores[str(d)] += 1.2
            for d in trans_all['sum_formulas']: digit_scores[d] += 1.2
            for d in trans_all['cross_formulas']: digit_scores[str(d)] += 1.0

            # --- น้ำหนักส่วนที่ 3: จากผลรายวันล่าสุด (+1.5 แต้ม) ---
            for d in trans_day['carry_over']: digit_scores[str(d)] += 1.5
            for d in trans_day['pm1']: digit_scores[str(d)] += 1.2
            for d in trans_day['sum_formulas']: digit_scores[d] += 1.2
            for d in trans_day['cross_formulas']: digit_scores[str(d)] += 1.0

            sorted_digits = sorted(
                digit_scores.keys(), key=lambda k: digit_scores[k], reverse=True
            )
            den = sorted_digits[0]
            rong_list = sorted_digits[1:4]
            gun_list = sorted_digits[4:7]

            st.markdown("---")
            st.success(f"🎯 **สรุปแนวทางเลขเด่นทำนายงวดถัดไป ({day_selected})**")
            col1, col2, col3 = st.columns(3)
            col1.metric("เด่น", den, f"{digit_scores[den]:.1f} แต้ม")
            col2.metric("รอง", " - ".join(rong_list))
            col3.metric("กัน", " - ".join(gun_list))

            suggested_2d = [f"{den}{r}" for r in rong_list] + [
                f"{r}{den}" for r in rong_list
            ]
            suggested_3d = [f"{den}{rong_list[0]}{rong_list[1]}"]
            suggested_double = [f"{den}{den}", f"{rong_list[0]}{rong_list[0]}"]

            st.write(f"• **ชุด 2 ตัวเน้นๆ (ไป-กลับ) :** {', '.join(suggested_2d)}")
            st.write(f"• **ชุด 3 ตัวบนแนะนำ        :** {', '.join(suggested_3d)}")
            st.write(f"• **ชุด 2 ตัวเบิ้ล (แนะนำ)    :** {', '.join(suggested_double)}")
    else:
        st.info("ยังไม่มีข้อมูลในระบบ กรุณาอัปเพิ่มในเมนูที่ 1 ก่อน")
