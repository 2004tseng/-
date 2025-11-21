import streamlit as st
import datetime
import json
import os
import random

# --- 配置參數 ---
DEFAULT_CYCLE = 28       
PERIOD_LENGTH = 5        
OVULATION_WINDOW_START_OFFSET = 16 
OVULATION_WINDOW_END_OFFSET = 12   
DATA_FILE = 'period_data.json' 

# --- 模擬笑話資料 ---
JOKES_LIST = [
    {"q": "布和紙怕什麼？", "a": "布怕一萬，紙怕萬一。 (不/布怕一萬，只/紙怕萬一)"},
    {"q": "什麼人是不用電的？", "a": "緬甸人 (免電人)"},
    {"q": "麒麟到了北極會變成什麼？", "a": "冰淇淋 (冰麒麟)"},
    {"q": "和尚打著一把傘，是一個什麼成語？", "a": "無法無天 (無發無天)"},
    {"q": "小明為什麼能用一隻手讓車子停下來？", "a": "搭計程車"},
    {"q": "什麼官不僅不領工資，還要自掏腰包？", "a": "新郎官"},
    {"q": "哪一種竹子不長在土裡？", "a": "爆竹"},
    {"q": "世界上什麼人一下子變老？", "a": "新娘 (今天是新娘，明天是老婆)"},
    {"q": "什麼動物可以貼在牆上？", "a": "海豹 (海報)"},
    {"q": "為什麼鎖匠比大學生更有學問？", "a": "因為他是研究所 (研究鎖) 的。"},
]

# --- 數據儲存與載入 ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data['cycles'] = [{'start': datetime.date.fromisoformat(c['start']), 
                               'end': datetime.date.fromisoformat(c['end']) if 'end' in c and c['end'] else None} 
                              for c in data['cycles']]
            return data
    return {'cycles': [], 'avg_cycle': DEFAULT_CYCLE}

def save_data(data):
    serializable_cycles = [{'start': c['start'].isoformat(), 
                            'end': c['end'].isoformat() if 'end' in c and c['end'] else None} 
                           for c in data['cycles']]
    data_to_save = {'cycles': serializable_cycles, 'avg_cycle': data['avg_cycle']}
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

def init_session_state():
    if 'data' not in st.session_state:
        st.session_state['data'] = load_data()
    
    st.session_state['data']['cycles'] = sorted(
        st.session_state['data']['cycles'], key=lambda x: x['start']
    )

# --- 核心計算功能 ---
def calculate_average_cycle_length(history_cycles):
    """計算並更新平均週期長度。"""
    if len(history_cycles) < 2:
        return DEFAULT_CYCLE
    cycle_lengths = []
    for i in range(1, len(history_cycles)):
        length = (history_cycles[i]['start'] - history_cycles[i-1]['start']).days
        if length > 0:
            cycle_lengths.append(length)
    if not cycle_lengths:
        return DEFAULT_CYCLE
    return round(sum(cycle_lengths) / len(cycle_lengths))

def get_phase_info(date_to_check, last_start_date, avg_cycle):
    """
    根據日期判斷週期階段，並附上提醒。
    **已修正：加入模數運算，支援無限期預測。**
    """
    if not last_start_date: 
        return "等待首次紀錄", "請先設定上次經期開始日期。", "gray"

    days_diff_raw = (date_to_check - last_start_date).days
    
    if days_diff_raw < 0:
        return "尚未開始新週期", "請確保查詢日期晚於上次經期開始日。", "gray"
    
    # 🌟 關鍵修正：使用模數運算來計算該日期落在「預測週期」的第幾天。
    # (days_diff_raw % avg_cycle) 得到 0 到 avg_cycle-1 的餘數
    # + 1 轉換為週期日 1 到 avg_cycle
    days_into_cycle = (days_diff_raw % avg_cycle) + 1 

    # --- 階段判斷邏輯 (使用修正後的 days_into_cycle) ---
    
    # 1. 經期
    if 1 <= days_into_cycle <= PERIOD_LENGTH:
        return "經期 (Menstrual Phase)", "多休息，注意保暖，避免劇烈運動。", "red"
    
    # 2. 排卵期計算
    ovulation_start_day = avg_cycle - OVULATION_WINDOW_START_OFFSET + 1
    ovulation_end_day = avg_cycle - OVULATION_WINDOW_END_OFFSET + 1
    
    if ovulation_start_day <= days_into_cycle <= ovulation_end_day:
        return "排卵期 (Ovulation Window)", "易受孕期！這幾天身體訊號較明顯，請多留意。", "green"
        
    # 3. 濾泡期
    if PERIOD_LENGTH < days_into_cycle < ovulation_start_day:
        return "濾泡期 (Follicular Phase)", "精神狀態佳，體力回升，是安排重要活動和運動的好時機！", "blue"
        
    # 4. 黃體期
    if ovulation_end_day <= days_into_cycle <= avg_cycle:
        return "黃體期 (Luteal Phase)", "情緒可能波動，身體為經期做準備，保持心情平靜，注意清淡飲食。", "purple"

    # 如果平均週期計算出問題，作為安全備援 (理論上不會觸發)
    return "週期計算範圍內", "保持健康生活習慣。", "gray"

# --- 趣味功能：每日笑話 (保持不變) ---
def display_daily_joke():
    """模擬每日更新的笑話欄位。"""
    today = datetime.date.today().isoformat()

    if 'joke_date' not in st.session_state or st.session_state['joke_date'] != today:
        st.session_state['joke_date'] = today
        st.session_state['current_joke'] = random.choice(JOKES_LIST)

    joke = st.session_state['current_joke']
    
    st.header("🤡 錄影中請微笑")
    st.markdown("### 🤣 每日一笑：")
    
    st.markdown(
        f"""
        <div style='background-color: #ffe5e5; padding: 15px; border-radius: 10px;'>
            <p style='font-size: 1.2em; font-weight: bold;'>🧠 提問：{joke['q']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.expander("點我看答案"):
        st.markdown(f"**💡 答案：** {joke['a']}")
    
    st.caption(f"內容更新於 {st.session_state['joke_date']}")
    st.markdown("---")


# --- Streamlit 應用程式主體 ---
def run_app():
    """Streamlit App 介面和功能整合。"""
    init_session_state()

    st.set_page_config(page_title="💖 俊瑋保命神器", layout="centered")
    st.title("💖 俊瑋保命神器")
    
    current_data = st.session_state['data']
    history_cycles = current_data['cycles']
    avg_cycle = current_data['avg_cycle']
    last_start_date = history_cycles[-1]['start'] if history_cycles else None

    # --- 1. 紀錄經期 (移至最上方) ---
    st.header("📝 紀錄經期 (讓預測更精準！)")
    
    with st.expander("點此紀錄/更新經期", expanded=not last_start_date): 
        st.subheader("設定本次經期紀錄")
        
        if history_cycles:
            st.info(f"上次紀錄的經期開始日：**{history_cycles[-1]['start'].strftime('%Y/%m/%d')}**")

        new_start_date = st.date_input("開始日期：", value=datetime.date.today())
        new_end_date = st.date_input("結束日期：", value=new_start_date + datetime.timedelta(days=PERIOD_LENGTH-1))
        
        if new_end_date < new_start_date:
            st.error("結束日期不能早於開始日期！")
            new_end_date = new_start_date 

        add_record_button = st.button(label='新增/更新本次經期紀錄')

        if add_record_button:
            if history_cycles and new_start_date <= history_cycles[-1]['start']:
                st.error("新的經期開始日期必須晚於您紀錄的最後一次經期開始日！")
            elif new_start_date > datetime.date.today():
                 st.warning("您不能紀錄未來的經期開始日！")
            else:
                history_cycles.append({'start': new_start_date, 'end': new_end_date})
                current_data['cycles'] = sorted(history_cycles, key=lambda x: x['start']) 
                current_data['avg_cycle'] = calculate_average_cycle_length(current_data['cycles'])
                
                save_data(current_data) 
                st.success(f"紀錄成功！平均週期已更新為 **{current_data['avg_cycle']}** 天。")
                
                st.rerun() 

    st.markdown("---")

    # --- 2. 今日資訊 ---
    st.header("✨ 今日資訊")
    if last_start_date:
        today_phase, today_note, color = get_phase_info(datetime.date.today(), last_start_date, avg_cycle)
        st.markdown(f"**今天 ({datetime.date.today().strftime('%Y/%m/%d')}) 屬於：** <span style='color:{color}; font-size: 1.2em;'>**{today_phase}**</span>", unsafe_allow_html=True)
        st.text(f"貼心提醒：{today_note}")
    else:
        st.info("請先設定上次經期開始日期，以獲取今日資訊。")

    st.markdown("---")

    # --- 3. 下次經期預測 ---
    st.header("🗓️ 下次經期預測")
    if last_start_date:
        next_start_date = last_start_date + datetime.timedelta(days=avg_cycle)
        days_to_next = (next_start_date - datetime.date.today()).days
        
        st.metric(label="預計下次經期開始日", value=next_start_date.strftime('%Y 年 %m 月 %d 日'))
        
        if days_to_next > 0:
            st.success(f"距離下次經期還有 **{days_to_next}** 天！")
        elif days_to_next == 0:
            st.error("預計今天就是經期開始日！")
        # 由於 get_phase_info 已修正，這裡的 days_to_next < 0 仍然是準確的
        else:
            st.warning(f"經期預計已遲到 {-days_to_next} 天。請留意身體狀況。")
            
        st.info(f"**平均週期：** {avg_cycle} 天 (基於 {len(history_cycles)} 次紀錄)")
    else:
        st.info("請先設定上次經期開始日期，以預測下次經期。")

    st.markdown("---")

    # --- 4. 查詢特定日期階段 ---
    st.header("🔎 查詢特定日期階段")
    with st.expander("點此查詢其他日期", expanded=False):
        if not last_start_date:
            st.warning("請先設定上次經期開始日期，才能查詢其他日期。")
        else:
            query_date = st.date_input("選擇您想查詢的日期：", value=datetime.date.today())
            
            if st.button("查詢該日期階段"):
                query_phase, query_note, query_color = get_phase_info(query_date, last_start_date, avg_cycle)
                
                # 重新計算下次開始日期，用於顯示距離
                days_diff_raw = (query_date - last_start_date).days
                current_cycle_start_diff = days_diff_raw - (days_diff_raw % avg_cycle)
                current_cycle_start = last_start_date + datetime.timedelta(days=current_cycle_start_diff)
                
                next_start_date = current_cycle_start + datetime.timedelta(days=avg_cycle)
                days_from_query_to_next = (next_start_date - query_date).days
                
                st.markdown(f"**查詢日期 ({query_date.strftime('%Y/%m/%d')}) 屬於：** <span style='color:{query_color}; font-size: 1.1em;'>**{query_phase}**</span>", unsafe_allow_html=True)
                st.text(f"注意事項：{query_note}")
                
                if days_from_query_to_next > 0:
                    st.success(f"距離下一個預計經期開始日還有 **{days_from_query_to_next}** 天。")
                elif days_from_query_to_next == 0:
                    st.warning("預計當天就是經期開始日。")
                else:
                    # 這一條應該不會出現，除非 query_date 比 next_start_date 還晚
                    st.info("已在預計經期內或之後。")


    st.markdown("---")

    # --- 5. 錄影中請微笑 ---
    display_daily_joke()


if __name__ == '__main__':
    run_app()