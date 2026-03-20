import streamlit as st
import random as r
import pandas as pd
import plotly.graph_objects as go
import requests

# --- API CONFIGURATION ---
API_URL = "https://cricket-api-backend-3zph.onrender.com" 

# --- 1. SETUP MEMORY (SESSION STATE) ---
if 'phase' not in st.session_state:
    st.session_state.phase = 'toss'
    st.session_state.l1 = 0 
    st.session_state.l2 = 0 
    st.session_state.wickets1 = 0
    st.session_state.wickets2 = 0
    st.session_state.timeline1 = [0]
    st.session_state.timeline2 = [0]
    st.session_state.balls1 = 0
    st.session_state.balls2 = 0
    st.session_state.target = 0
    st.session_state.user_bat_inning = 0
    
    st.session_state.d1 = {}
    st.session_state.d11 = {}
    st.session_state.d2 = {}
    st.session_state.d22 = {}
    
    st.session_state.userbatting = {1:"Virat Kohli", 2:"Rohit Sharma", 3:"Dhoni", 4:"Hardik", 5:"Jadeja"}
    st.session_state.userbowling = {1:"Bumrah", 2:"Chahal", 3:"Siraj", 4:"Kuldeep", 5:"Hardik"}
    st.session_state.sysbatting = {1:'Travis Head', 2:'Steve Smith', 3:'Mitchell Marsh', 4:'Cameron Green', 5:'Josh Inglis'}
    st.session_state.sysbowling = {1:'Pat Cummins', 2:'Mitchell Starc', 3:'Josh Hazlewood', 4:'Nathan Lyon', 5:'Adam Zampa'}
    
    st.session_state.curr_bat = None
    st.session_state.curr_bowl = None
    st.session_state.curr_bat_runs = 0
    st.session_state.curr_bat_balls = 0
    st.session_state.last_over_balls = 0
    
    st.session_state.show_bat_stats = False
    st.session_state.show_bowl_stats = False

    st.session_state.toss_won_by_user = None
    st.session_state.toss_sys_num = 0
    st.session_state.toss_total = 0
    st.session_state.toss_user_call = ""
    st.session_state.toss_user_num = 0

    st.session_state.out_batsman = ""
    st.session_state.out_bowler = ""
    st.session_state.return_phase = ""
    st.session_state.after_break_phase = "" 
    st.session_state.break_msg = "" 
    st.session_state.is_all_out = False # Tracks if it's the final wicket

# --- HELPER FUNCTIONS ---
def update_bowling(dict_name, bowler, balls, runs, wickets):
    if bowler not in st.session_state[dict_name]:
        st.session_state[dict_name][bowler] = [0, 0, 0, 0.0]
    st.session_state[dict_name][bowler][0] += balls
    st.session_state[dict_name][bowler][1] += runs
    st.session_state[dict_name][bowler][2] += wickets

def save_batsman(dict_name, batsman, runs, balls):
    avg = round((runs / balls) * 100, 2) if balls > 0 else 0
    st.session_state[dict_name][batsman] = [runs, balls, avg]

def fetch_career_stats(player_name, role, is_user):
    try:
        # INCREASED TIMEOUT: Gives Render API 15 seconds to wake up from sleep!
        res = requests.post(f"{API_URL}/get_stats", json={"player_name": player_name, "role": role, "is_user": is_user}, timeout=15)
        if res.status_code == 200 and len(res.json()) > 0:
            stats = res.json()[0]
            st.markdown(f"**📊 {player_name.upper()} ({'Career Batting' if role=='bat' else 'Career Bowling'})**")
            cols = st.columns(len(stats))
            for idx, (key, value) in enumerate(stats.items()):
                cols[idx].metric(key, value)
        else:
            st.info(f"📊 **{player_name}:** No DB records found. (If this is a bug, save a match first!)")
    except Exception as e:
        st.warning(f"⚠️ Waking up Render Database for {player_name}... This may take 10 seconds.")

def format_bowling_card(raw_dict):
    if not raw_dict:
        return pd.DataFrame(columns=['Overs', 'Runs', 'Wickets', 'Economy'])
    df = pd.DataFrame.from_dict(raw_dict, orient='index', columns=['Balls', 'Runs', 'Wickets', 'Economy'])
    df['Overs'] = df['Balls'].apply(lambda b: f"{b//6}.{b%6}")
    df['Economy'] = df.apply(lambda row: round(row['Runs'] / (row['Balls']/6), 2) if row['Balls'] > 0 else 0.00, axis=1)
    return df[['Overs', 'Runs', 'Wickets', 'Economy']]

# --- UI: MAIN BANNER ---
st.set_page_config(page_title="Khushal's Hand Cricket", page_icon="🏏", layout="centered")
if st.session_state.phase not in ['wicket_screen', 'innings_break']:
    st.title("🏏 Khushal's Hand Cricket Clash")
    st.write("---")

# --- PHASE: WICKET SCREEN ---
if st.session_state.phase == 'wicket_screen':
    st.markdown("<br><br><br>", unsafe_allow_html=True) 
    
    # DYNAMIC ALL OUT HEADER
    if st.session_state.is_all_out:
        st.markdown("<h1 style='text-align: center; color: #ff4b4b; font-size: 90px;'>🚨 ALL OUT! 🚨</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #ff4b4b; font-size: 80px;'>🚨 WICKET! 🚨</h1>", unsafe_allow_html=True)
        
    st.markdown(f"<h2 style='text-align: center;'>{st.session_state.out_batsman} has been dismissed!</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>Bowled by: {st.session_state.out_bowler}</h3>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    btn_txt = "➡️ Continue to Innings Break" if st.session_state.is_all_out else "➡️ Bring in the Next Batsman"
    if col2.button(btn_txt, use_container_width=True):
        st.session_state.phase = st.session_state.return_phase
        st.rerun()

# --- PHASE: INNINGS BREAK ---
elif st.session_state.phase == 'innings_break':
    st.markdown("<br><br><br>", unsafe_allow_html=True) 
    st.markdown(f"<h1 style='text-align: center; color: #ffeb3b; font-size: 70px;'>🔄 {st.session_state.break_msg} 🔄</h1>", unsafe_allow_html=True)
    
    current_score = st.session_state.l1 if st.session_state.after_break_phase == 'inning2_sys_bat' else st.session_state.l2
    st.markdown(f"<h2 style='text-align: center;'>Final Innings Score: {current_score}</h2>", unsafe_allow_html=True)
    
    if st.session_state.target > 0 and st.session_state.after_break_phase != 'match_over':
        st.markdown(f"<h2 style='text-align: center; color: #ff4b4b;'>Target to win: {st.session_state.target} runs</h2>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    btn_text = "➡️ Start Next Innings" if st.session_state.after_break_phase != 'match_over' else "➡️ View Match Results"
    if col2.button(btn_text, use_container_width=True):
        st.session_state.phase = st.session_state.after_break_phase
        st.rerun()

# --- PHASE: TOSS ---
elif st.session_state.phase == 'toss':
    st.header("🪙 The Toss")
    if st.session_state.toss_won_by_user is None:
        col1, col2 = st.columns(2)
        with col1:
            n = st.radio("Call it:", ["Even", "Odd"])
        with col2:
            num = st.number_input("Enter a number (1-10):", min_value=1, max_value=10, step=1)
        
        if st.button("Flip Coin!", use_container_width=True):
            num1 = r.randint(1,10)
            st.session_state.toss_sys_num = num1
            st.session_state.toss_user_num = num
            st.session_state.toss_user_call = n
            st.session_state.toss_total = num + num1
            is_even = ((num + num1) % 2 == 0)
            st.session_state.toss_won_by_user = (n == "Even" and is_even) or (n == "Odd" and not is_even)
            st.rerun()
    else:
        st.markdown("<h2 style='text-align: center;'>🪙 TOSS RESULT 🪙</h2>", unsafe_allow_html=True)
        st.info(f"**You called:** {st.session_state.toss_user_call} | **You played:** {st.session_state.toss_user_num}")
        st.info(f"**Opponent played:** {st.session_state.toss_sys_num} | **Total:** {st.session_state.toss_total}")
        
        if st.session_state.toss_won_by_user:
            st.success("🎉 **YOU WON THE TOSS!** 🎉")
            st.write("### What will you choose to do?")
            col1, col2 = st.columns(2)
            if col1.button("🏏 Bat First", use_container_width=True):
                st.session_state.user_bat_inning = 1
                st.session_state.phase = 'inning1_user_bat'
                st.rerun()
            if col2.button("🥎 Bowl First", use_container_width=True):
                st.session_state.user_bat_inning = 2
                st.session_state.phase = 'inning1_sys_bat'
                st.rerun()
        else:
            sys_choice = r.choice(["Bat", "Bowl"])
            st.error(f"💀 **YOU LOST THE TOSS.** Opponent elected to **{sys_choice}** first.")
            if st.button("Start Match", use_container_width=True):
                if sys_choice == "Bat":
                    st.session_state.user_bat_inning = 2
                    st.session_state.phase = 'inning1_sys_bat'
                else:
                    st.session_state.user_bat_inning = 1
                    st.session_state.phase = 'inning1_user_bat'
                st.rerun()

# --- PHASE: USER BATTING ---
elif st.session_state.phase in ['inning1_user_bat', 'inning2_user_bat']:
    st.markdown(f"<h2 style='text-align: center; color: #1f77b4;'>INDIA BATTING: {st.session_state.l1} / {st.session_state.wickets1}</h2>", unsafe_allow_html=True)
    
    overs = st.session_state.balls1 // 6
    balls = st.session_state.balls1 % 6
    colA, colB, colC = st.columns(3)
    colA.metric("Overs", f"{overs}.{balls} / 5.0")
    colB.metric("Current Run Rate", round((st.session_state.l1 / st.session_state.balls1) * 6, 2) if st.session_state.balls1 > 0 else 0.00)
    if st.session_state.target > 0:
        colC.metric("Target", st.session_state.target, f"{(st.session_state.target - st.session_state.l1)} runs needed", delta_color="inverse")
    st.write("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.curr_bat is None:
            selected_bat = st.selectbox("Select Batsman:", list(st.session_state.userbatting.values()), index=None, placeholder="Choose your batsman...")
            if selected_bat:
                st.session_state.curr_bat = selected_bat
                st.session_state.show_bat_stats = True
                st.rerun() 
        else:
            st.markdown(f"#### 🏏 Batsman: **{st.session_state.curr_bat}**")

    with col2:
        if st.session_state.curr_bowl is None:
            st.session_state.curr_bowl = r.choice(list(st.session_state.sysbowling.values()))
            st.session_state.last_over_balls = 0
            st.session_state.show_bowl_stats = True
            st.toast(f"🏏 Match Starts! Opening Bowler: {st.session_state.curr_bowl}", icon="🏏")
        elif st.session_state.balls1 > 0 and st.session_state.balls1 % 6 == 0 and st.session_state.last_over_balls != st.session_state.balls1:
            st.session_state.curr_bowl = r.choice(list(st.session_state.sysbowling.values()))
            st.session_state.last_over_balls = st.session_state.balls1
            st.session_state.show_bowl_stats = True
            st.toast(f"🔄 OVER COMPLETE! New Bowler: {st.session_state.curr_bowl}", icon="🔄")
            
        if st.session_state.curr_bowl:
            st.markdown(f"#### 🥎 Bowler: **{st.session_state.curr_bowl}**")

    if st.session_state.show_bat_stats or st.session_state.show_bowl_stats:
        with st.container(border=True):
            if st.session_state.show_bat_stats and st.session_state.curr_bat:
                fetch_career_stats(st.session_state.curr_bat, "bat", True)
            if st.session_state.show_bowl_stats and st.session_state.curr_bowl:
                st.write("") 
                fetch_career_stats(st.session_state.curr_bowl, "bowl", False)

    if st.session_state.curr_bat is None:
        st.warning("⚠️ Waiting for captain... Please select a Batsman to continue the innings!")
    else:
        st.write("### Play your shot:")
        cols = st.columns(6)
        for i in range(1, 7):
            if cols[i-1].button(str(i), key=f"bat_{i}", use_container_width=True):
                st.session_state.show_bat_stats = False 
                st.session_state.show_bowl_stats = False
                
                sys_bowl = r.randint(1,6)
                st.session_state.balls1 += 1
                st.session_state.curr_bat_balls += 1
                is_wicket = (i == sys_bowl)
                
                if is_wicket:
                    st.session_state.wickets1 += 1
                    update_bowling('d22', st.session_state.curr_bowl, 1, 0, 1)
                    save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    st.session_state.out_batsman = st.session_state.curr_bat
                    st.session_state.out_bowler = st.session_state.curr_bowl
                    st.session_state.userbatting = {k:v for k,v in st.session_state.userbatting.items() if v != st.session_state.curr_bat}
                    st.session_state.timeline1.append(st.session_state.l1)
                else:
                    st.success(f"Opponent bowled {sys_bowl}. You scored **{i}** runs!")
                    st.session_state.l1 += i
                    st.session_state.curr_bat_runs += i
                    update_bowling('d22', st.session_state.curr_bowl, 1, i, 0)
                    st.session_state.timeline1.append(st.session_state.l1)
                    
                innings_over = not st.session_state.userbatting or st.session_state.balls1 >= 30 or (st.session_state.target > 0 and st.session_state.l1 >= st.session_state.target)
                
                # Setup Next Phase Destiny
                if st.session_state.phase == 'inning1_user_bat':
                    final_dest = 'inning2_sys_bat'
                else:
                    final_dest = 'match_over'

                if innings_over:
                    if not is_wicket and st.session_state.curr_bat in st.session_state.userbatting.values():
                        save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    if st.session_state.phase == 'inning1_user_bat': st.session_state.target = st.session_state.l1 + 1
                    
                    st.session_state.is_all_out = not bool(st.session_state.userbatting)
                    st.session_state.break_msg = "ALL OUT!" if st.session_state.is_all_out else "INNINGS OVER!"
                    
                    st.session_state.curr_bowl = None
                    st.session_state.curr_bat = None 
                    st.session_state.last_over_balls = 0
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    
                    if is_wicket:
                        st.session_state.phase = 'wicket_screen'
                        st.session_state.return_phase = 'innings_break'
                        st.session_state.after_break_phase = final_dest
                    else:
                        st.session_state.phase = 'innings_break'
                        st.session_state.after_break_phase = final_dest
                        
                elif is_wicket:
                    st.session_state.is_all_out = False
                    st.session_state.curr_bat = None 
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    st.session_state.phase = 'wicket_screen'
                    st.session_state.return_phase = st.session_state.phase

                st.rerun()

# --- PHASE: SYSTEM BATTING ---
elif st.session_state.phase in ['inning1_sys_bat', 'inning2_sys_bat']:
    st.markdown(f"<h2 style='text-align: center; color: #ff7f0e;'>AUSTRALIA BATTING: {st.session_state.l2} / {st.session_state.wickets2}</h2>", unsafe_allow_html=True)
    
    overs = st.session_state.balls2 // 6
    balls = st.session_state.balls2 % 6
    colA, colB, colC = st.columns(3)
    colA.metric("Overs", f"{overs}.{balls} / 5.0")
    colB.metric("Current Run Rate", round((st.session_state.l2 / st.session_state.balls2) * 6, 2) if st.session_state.balls2 > 0 else 0.00)
    if st.session_state.target > 0:
        colC.metric("Target", st.session_state.target, f"{(st.session_state.target - st.session_state.l2)} runs needed", delta_color="inverse")
    st.write("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.curr_bat is None or st.session_state.curr_bat not in st.session_state.sysbatting.values():
            if st.session_state.sysbatting:
                st.session_state.curr_bat = r.choice(list(st.session_state.sysbatting.values()))
                st.session_state.show_bat_stats = True
        if st.session_state.curr_bat:
            st.markdown(f"#### 🏏 Opponent Batsman: **{st.session_state.curr_bat}**")

    with col2:
        need_new_bowler = False
        if st.session_state.curr_bowl is None:
            need_new_bowler = True
        elif st.session_state.balls2 > 0 and st.session_state.balls2 % 6 == 0 and st.session_state.last_over_balls != st.session_state.balls2:
            st.session_state.curr_bowl = None 
            st.session_state.last_over_balls = st.session_state.balls2
            st.toast("🔄 OVER COMPLETE! Pick your next bowler.", icon="🔄")
            need_new_bowler = True
            
        if need_new_bowler or st.session_state.curr_bowl is None:
            selected_bowl = st.selectbox("Select your Bowler:", list(st.session_state.userbowling.values()), index=None, placeholder="Hand the ball to...")
            if selected_bowl:
                st.session_state.curr_bowl = selected_bowl
                st.session_state.show_bowl_stats = True 
                st.rerun() 
        else:
            st.markdown(f"#### 🥎 Bowler: **{st.session_state.curr_bowl}**")

    if st.session_state.show_bat_stats or st.session_state.show_bowl_stats:
        with st.container(border=True):
            if st.session_state.show_bat_stats and st.session_state.curr_bat:
                fetch_career_stats(st.session_state.curr_bat, "bat", False)
            if st.session_state.show_bowl_stats and st.session_state.curr_bowl:
                st.write("")
                fetch_career_stats(st.session_state.curr_bowl, "bowl", True)

    if st.session_state.curr_bowl is None:
        st.warning("⚠️ Waiting for captain... Please select a Bowler to continue the over!")
    else:
        st.write("### Bowl your delivery:")
        cols = st.columns(6)
        for i in range(1, 7):
            if cols[i-1].button(str(i), key=f"bowl_{i}", use_container_width=True):
                st.session_state.show_bat_stats = False
                st.session_state.show_bowl_stats = False
                
                sys_bat = r.randint(1,6)
                st.session_state.balls2 += 1
                st.session_state.curr_bat_balls += 1
                is_wicket = (i == sys_bat)
                
                if is_wicket:
                    st.session_state.wickets2 += 1
                    update_bowling('d11', st.session_state.curr_bowl, 1, 0, 1)
                    save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    st.session_state.out_batsman = st.session_state.curr_bat
                    st.session_state.out_bowler = st.session_state.curr_bowl
                    st.session_state.sysbatting = {k:v for k,v in st.session_state.sysbatting.items() if v != st.session_state.curr_bat}
                    st.session_state.timeline2.append(st.session_state.l2)
                    
                else:
                    st.warning(f"Opponent played {sys_bat}. They scored **{sys_bat}** runs.")
                    st.session_state.l2 += sys_bat
                    st.session_state.curr_bat_runs += sys_bat
                    update_bowling('d11', st.session_state.curr_bowl, 1, sys_bat, 0)
                    st.session_state.timeline2.append(st.session_state.l2)
                    
                innings_over = not st.session_state.sysbatting or st.session_state.balls2 >= 30 or (st.session_state.target > 0 and st.session_state.l2 >= st.session_state.target)
                
                if st.session_state.phase == 'inning1_sys_bat':
                    final_dest = 'inning2_user_bat'
                else:
                    final_dest = 'match_over'

                if innings_over:
                    if not is_wicket and st.session_state.curr_bat in st.session_state.sysbatting.values():
                        save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    if st.session_state.phase == 'inning1_sys_bat': st.session_state.target = st.session_state.l2 + 1
                    
                    st.session_state.is_all_out = not bool(st.session_state.sysbatting)
                    st.session_state.break_msg = "ALL OUT!" if st.session_state.is_all_out else "INNINGS OVER!"
                    
                    st.session_state.curr_bowl = None
                    st.session_state.curr_bat = None 
                    st.session_state.last_over_balls = 0
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    
                    if is_wicket:
                        st.session_state.phase = 'wicket_screen'
                        st.session_state.return_phase = 'innings_break'
                        st.session_state.after_break_phase = final_dest
                    else:
                        st.session_state.phase = 'innings_break'
                        st.session_state.after_break_phase = final_dest
                        
                elif is_wicket:
                    st.session_state.is_all_out = False
                    st.session_state.curr_bat = None 
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    st.session_state.phase = 'wicket_screen'
                    st.session_state.return_phase = st.session_state.phase

                st.rerun()

# --- PHASE: MATCH OVER ---
elif st.session_state.phase == 'match_over':
    st.header("🏆 MATCH FINISHED")
    
    if st.session_state.l1 > st.session_state.l2:
        st.success(f"🎉 **India won by {st.session_state.l1 - st.session_state.l2} runs!**")
    elif st.session_state.l2 > st.session_state.l1:
        st.error(f"💀 **Australia won by {5 - st.session_state.wickets2} wickets!**")
    else:
        st.info("🤝 **The match is a Draw!**")

    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏏 India Batting")
        st.dataframe(pd.DataFrame.from_dict(st.session_state.d1, orient='index', columns=['Runs', 'Balls', 'Strike Rate']), use_container_width=True)
        st.subheader("🥎 India Bowling")
        st.dataframe(format_bowling_card(st.session_state.d11), use_container_width=True)

    with col2:
        st.subheader("🏏 Australia Batting")
        st.dataframe(pd.DataFrame.from_dict(st.session_state.d2, orient='index', columns=['Runs', 'Balls', 'Strike Rate']), use_container_width=True)
        st.subheader("🥎 Australia Bowling")
        st.dataframe(format_bowling_card(st.session_state.d22), use_container_width=True)

    st.write("---")
    st.subheader("📈 Run Chase Flow")
    fig = go.Figure()
    
    fig = go.Figure()
    
    # 1. Create custom text that ONLY exists on wicket balls, empty everywhere else
    custom1 = ["🚨 WICKET!" if (i > 0 and st.session_state.timeline1[i] == st.session_state.timeline1[i-1]) else "" for i in range(len(st.session_state.timeline1))]
    custom2 = ["🚨 WICKET!" if (i > 0 and st.session_state.timeline2[i] == st.session_state.timeline2[i-1]) else "" for i in range(len(st.session_state.timeline2))]

    # 2. Main Lines (We inject the custom text directly into the hover template here)
    fig.add_trace(go.Scatter(
        x=list(range(len(st.session_state.timeline1))), y=st.session_state.timeline1, mode='lines', name='India Runs', 
        line=dict(color='#1f77b4', width=3),
        customdata=custom1,
        hovertemplate="<b>India</b><br>Ball: %{x}<br>Score: %{y} <span style='color:#ff4b4b'><b>%{customdata}</b></span><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(st.session_state.timeline2))), y=st.session_state.timeline2, mode='lines', name='Australia Runs', 
        line=dict(color='#ff7f0e', width=3, dash='dash'),
        customdata=custom2,
        hovertemplate="<b>Australia</b><br>Ball: %{x}<br>Score: %{y} <span style='color:#ff4b4b'><b>%{customdata}</b></span><extra></extra>"
    ))

    # 3. Calculate Wicket Coordinates
    w_x1 = [i for i in range(1, len(st.session_state.timeline1)) if st.session_state.timeline1[i] == st.session_state.timeline1[i-1]]
    w_y1 = [st.session_state.timeline1[i] for i in w_x1]
    w_x2 = [i for i in range(1, len(st.session_state.timeline2)) if st.session_state.timeline2[i] == st.session_state.timeline2[i-1]]
    w_y2 = [st.session_state.timeline2[i] for i in w_x2]

    # 4. Draw the Wicket Markers (hoverinfo='skip' completely disables their annoying ghost boxes!)
    if w_x1:
        fig.add_trace(go.Scatter(x=w_x1, y=w_y1, mode='markers', name='India Wickets', marker=dict(color='red', size=12, symbol='x', line=dict(width=2, color='white')), hoverinfo='skip'))
    if w_x2:
        fig.add_trace(go.Scatter(x=w_x2, y=w_y2, mode='markers', name='Australia Wickets', marker=dict(color='black', size=12, symbol='x', line=dict(width=2, color='white')), hoverinfo='skip'))

    # 5. Graph Formatting
    max_balls = max(len(st.session_state.timeline1), len(st.session_state.timeline2))
    fig.update_layout(xaxis_title="Balls Bowled", yaxis_title="Runs Scored", hovermode="x unified", xaxis=dict(tickmode='linear', tick0=0, dtick=6, range=[0, max_balls + 1]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    for over_mark in range(6, max_balls + 1, 6):
        fig.add_vline(x=over_mark, line_width=1, line_dash="dot", line_color="gray", opacity=0.4)

    st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    if not st.session_state.match_saved:
        if st.button("💾 Save Match Stats to Cloud", use_container_width=True):
            payload = {"d1": st.session_state.d1, "d11": st.session_state.d11, "d2": st.session_state.d2, "d22": st.session_state.d22}
            with st.spinner("Connecting to Aiven Database via Flask..."):
                try:
                    res = requests.post(f"{API_URL}/save_match", json=payload)
                    if res.status_code == 200:
                        st.session_state.match_saved = True
                        st.rerun() # Refresh the page to hide the button!
                    else:
                        st.error("Failed to save to database. Please try again.")
                except:
                    st.error("Failed to connect to the Server. Ensure Render API is awake.")
    else:
        st.success("✅ Match Data Safely Stored in Aiven Database!")
    st.write("---")
    if st.button("🔄 Play Again", type="primary", use_container_width=True):
        st.session_state.clear()
