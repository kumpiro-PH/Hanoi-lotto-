# app.py
import streamlit as st
import pandas as pd
from hanoi_formulas import (
    CSV_FILE, 
    initialize_csv, 
    parse_thai_date, 
    get_transformations, 
    DAILY_NUMBERS
)

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Hanoi AI Professional", page_icon="🎯", layout="wide")

# ตรวจสอบและสร้างฐานข้อมูลเริ่มต้น
initialize_csv()

st.title("🎯 Hanoi AI Professional - ระบบวิเคราะห์หวยฮานอย")
st.write("ระบบวิเคราะห์สถิติและทำนายแนวทางหวยฮานอยด้วย Python และ Streamlit")

# เมนูด้านข้าง (Sidebar)
menu = st.sidebar.selectbox(
    "เลือกเมนูการใช้งาน",
    [
        "1. อัปเดตผลรางวัล",
        "2. แสดงประวัติ (History)",
        "3. ลบข้อมืองวดล่าสุด",
        "4. Formula Ranking (จัดอันดับสูตร)",
        "5. Forward Prediction (ทำนายงวดถัดไป)"
    ]
)

# โหลดข้อมูล CSV
try:
    df_main = pd.read_csv(CSV_FILE)
except Exception:
    df_main = pd.DataFrame(columns=["date", "special", "first_prize", "top_3", "bottom_2"])

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
                new_row = pd.DataFrame([{
                    "date": date_str,
                    "special": special,
                    "first_prize": first_prize,
                    "top_3": top_3,
                    "bottom_2": bottom_2,
                }])
                updated_df = pd.concat([new_row, df_main], ignore_index=True)
                updated_df.to_csv(CSV_FILE, index=False)
                st.success("✅ บันทึกผลรางวัลใหม่สำเร็จเรียบร้อยแล้ว!")
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
            df = pd.read_csv(CSV_FILE)
            df["dt"] = df["date"].apply(parse_thai_date)
            df = df.dropna(subset=["dt"]).sort_values(by="dt", ascending=True).reset_index(drop=True)
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

                    if any(str(d) in t3 or str(d) in b2 for d in trans["carry_over"]): scores["Carry Over (ดึงเลขเก่า)"] += 1
                    if any(str(d) in t3 or str(d) in b2 for d in trans["pm1"]): scores["±1 (วิ่ง/รูด)"] += 1
                    if any(str(d) in t3 or str(d) in b2 for d in trans["sum_formulas"]): scores["Sum Modulo (ผลรวม)"] += 1
                    if any(str(d) in t3 or str(d) in b2 for d in trans["cross_formulas"]): scores["Cross Sum (สูตรไขว้)"] += 1
                    if any(c in t3 or c in b2 for c in daily_6): scores["Daily 6-Digit"] += 1
                    if any(rot in t3 for rot in trans["rotations"]) or any(any(c in b2 for c in rot) for rot in trans["rotations"]): scores["Rotation (โต๊ด)"] += 1
                    if any(c in t3 or c in b2 for c in trans["mirror"]): scores["Mirror (กระจก)"] += 1
                    if any(c in t3 or c in b2 for c in trans["shifted"]): scores["Shift (+2)"] += 1
                    if any(dbl in t3 or dbl in b2 for dbl in trans["doubles"]): scores["Double (เบิ้ล)"] += 1
                    if any(snd in t3 for snd in trans["sandwiches"]): scores["Sandwich (หาม)"] += 1

                ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                
                result_data = []
                for rank, (formula, score) in enumerate(ranked, 1):
                    percentage = (score / total) * 100
                    result_data.append({
                        "อันดับ": rank,
                        "ชื่อสูตร": formula,
                        "คะแนนที่ถูก": f"{score}/{total}",
                        "ความแม่นยำ (%)": f"{percentage:.1f}%"
                    })
                
                st.table(pd.DataFrame(result_data))

# เมนูที่ 5: ทำนายงวดถัดไป
elif menu == "5. Forward Prediction (ทำนายงวดถัดไป)":
    st.header("🔮 Forward Prediction (ทำนายแนวทางงวดถัดไป)")
    
    if not df_main.empty:
        latest = df_main.iloc[0]
        st.write(f"📅 ข้อมูลงวดล่าสุดวันที่: **{latest['date']}**")
        st.write(f"3 ตัวบน: `{latest['top_3']}` | 2 ตัวล่าง: `{latest['bottom_2']}`")
        
        day_selected = st.selectbox(
            "เลือกวันของงวดถัดไป",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )
        
        if st.button("ประมวลผลทำนายเลข"):
            daily_6 = DAILY_NUMBERS.get(day_selected, "000000")
            if day_selected == "Saturday":
                st.warning("⚠️ [AI WARNING] วันเสาร์มีสถิติการออก 'เลขเบิ้ล' และ 'เลขหาม' สูงมาก แนะนำให้ติดชุดกันไว้เสมอ!")
                
            trans = get_transformations(latest['top_3'], latest['bottom_2'])
            carry_list = sorted(list(trans['carry_over']))
            pm1_list = sorted(list(trans['pm1']))
            sum_list = sorted(list(trans['sum_formulas']))
            cross_list = sorted(list(trans['cross_formulas']))
            
            digit_scores = {str(i): 0.0 for i in range(10)}
            for d in daily_6: digit_scores[d] += 2.0
            for d in carry_list: digit_scores[str(d)] += 2.0
            for d in pm1_list: digit_scores[str(d)] += 1.5
            for d in sum_list: digit_scores[d] += 1.5
            for d in cross_list: digit_scores[str(d)] += 1.0
            for d in trans['mirror']: digit_scores[d] += 1.0
            for d in trans['shifted']: digit_scores[d] += 1.0

            sorted_digits = sorted(digit_scores.keys(), key=lambda k: digit_scores[k], reverse=True)
            den = sorted_digits[0]
            rong_list = sorted_digits[1:4]
            gun_list = sorted_digits[4:7]
            
            st.success(f"🎯 **สรุปแนวทางเลขเด่นทำนายงวดถัดไป ({day_selected})**")
            col1, col2, col3 = st.columns(3)
            col1.metric("เด่น", den, f"{digit_scores[den]:.1f} แต้ม")
            col2.metric("รอง", " - ".join(rong_list))
            col3.metric("กัน", " - ".join(gun_list))
            
            suggested_2d = [f"{den}{r}" for r in rong_list] + [f"{r}{den}" for r in rong_list]
            suggested_3d = [f"{den}{rong_list[0]}{rong_list[1]}"]
            suggested_double = [f"{den}{den}", f"{rong_list[0]}{rong_list[0]}"]
            
            st.markdown("---")
            st.write(f"• **ชุด 2 ตัวเน้นๆ (ไป-กลับ) :** {', '.join(suggested_2d)}")
            st.write(f"• **ชุด 3 ตัวบนแนะนำ        :** {', '.join(suggested_3d)}")
            st.write(f"• **ชุด 2 ตัวเบิ้ล (แนะนำ)    :** {', '.join(suggested_double)}")
    else:
        st.info("ยังไม่มีข้อมูลในระบบ กรุณาอัปเพิ่มในเมนูที่ 1 ก่อน")
