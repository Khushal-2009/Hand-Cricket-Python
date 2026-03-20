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
    
    # NEW: Trackers for stats display and avoiding pre-selection
    st.session_state.show_stats = False
    st.session_state.last_selected_bat = None
    st.session_state.last_selected_bowl = None

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
        res = requests.post(f"{API_URL}/get_stats", json={"player_name": player_name, "role": role, "is_user": is_user}, timeout=3)
        if res.status_code == 200 and len(res.json()) > 0:
            stats = res.json()[0]
            st.sidebar.markdown(f"### 📊 {player_name.upper()} ({'Batting' if role=='bat' else 'Bowling'})")
            for key, value in stats.items():
                st.sidebar.write(f"**{key}:** {value}")
        else:
            st.sidebar.info(f"{player_name}: Debut match! No prior stats.")
    except:
        pass 

# --- UI: MAIN BANNER ---
st.set_page_config(page_title="Khushal's Hand Cricket", page_icon="🏏", layout="centered")
st.title("🏏 Khushal's Hand Cricket Clash")
st.write("---")

# --- PHASE: TOSS ---
if st.session_state.phase == 'toss':
    st.header("🪙 The Toss")
    col1, col2 = st.columns(2)
    with col1:
        n = st.radio("Call it:", ["Even", "Odd"])
    with col2:
        num = st.number_input("Enter a number (1-10):", min_value=1, max_value=10, step=1)
    
    if st.button("Flip Coin!", use_container_width=True):
        num1 = r.randint(1,10)
        total = num + num1
        st.info(f"Opponent chose: **{num1}** | Total: **{total}**")
        
        is_even = (total % 2 == 0)
        user_won = (n == "Even" and is_even) or (n == "Odd" and not is_even)
        
        if user_won:
            st.success("🎉 You won the toss and elected to Bat first!")
            st.session_state.user_bat_inning = 1
            st.session_state.phase = 'inning1_user_bat'
            st.rerun()
        else:
            st.error("💀 You lost the toss. Opponent elected to Bat first.")
            st.session_state.user_bat_inning = 2
            st.session_state.phase = 'inning1_sys_bat'
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
        # NO PRE-SELECTION: index=None forces the user to pick!
        st.session_state.curr_bat = st.selectbox("Select Batsman:", list(st.session_state.userbatting.values()), index=None, placeholder="Choose your batsman...")
        
        # If new batsman selected, show stats
        if st.session_state.curr_bat != st.session_state.last_selected_bat and st.session_state.curr_bat is not None:
            st.session_state.show_stats = True
            st.session_state.last_selected_bat = st.session_state.curr_bat

    with col2:
        if st.session_state.curr_bowl is None or (st.session_state.balls1 > 0 and st.session_state.balls1 % 6 == 0 and st.session_state.last_over_balls != st.session_state.balls1):
            st.session_state.curr_bowl = r.choice(list(st.session_state.sysbowling.values()))
            st.session_state.last_over_balls = st.session_state.balls1
            st.session_state.show_stats = True # Show stats for new bowler!
            st.toast(f"🔄 OVER COMPLETE! New Bowler: {st.session_state.curr_bowl}", icon="🔄")
            
        if st.session_state.curr_bowl:
            st.markdown(f"#### 🥎 Bowler: **{st.session_state.curr_bowl}**")

    # Display Career Stats ONLY when show_stats is True
    if st.session_state.show_stats and st.session_state.curr_bat and st.session_state.curr_bowl:
        st.sidebar.header("📋 Pre-Delivery Stats")
        fetch_career_stats(st.session_state.curr_bat, "bat", True)
        fetch_career_stats(st.session_state.curr_bowl, "bowl", False)

    # Hide game buttons until a batsman is selected!
    if st.session_state.curr_bat is None:
        st.warning("⚠️ Waiting for captain... Please select a Batsman to continue the innings!")
    else:
        st.write("### Play your shot:")
        cols = st.columns(6)
        for i in range(1, 7):
            if cols[i-1].button(str(i), key=f"bat_{i}", use_container_width=True):
                st.session_state.show_stats = False # HIDE STATS IMMEDIATELY ON CLICK
                sys_bowl = r.randint(1,6)
                st.session_state.balls1 += 1
                st.session_state.curr_bat_balls += 1
                
                if i == sys_bowl:
                    st.toast("WICKET!!!", icon="🚨")
                    st.error(f"🚨 **WICKET!** Opponent bowled {sys_bowl}. **{st.session_state.curr_bat}** is OUT!")
                    
                    st.session_state.wickets1 += 1
                    update_bowling('d22', st.session_state.curr_bowl, 1, 0, 1)
                    save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    st.session_state.userbatting = {k:v for k,v in st.session_state.userbatting.items() if v != st.session_state.curr_bat}
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    st.session_state.timeline1.append(st.session_state.l1)
                    st.session_state.curr_bat = None # Force new selection
                    
                else:
                    st.success(f"Opponent bowled {sys_bowl}. You scored **{i}** runs!")
                    st.session_state.l1 += i
                    st.session_state.curr_bat_runs += i
                    st.session_state.timeline1.append(st.session_state.l1)
                    update_bowling('d22', st.session_state.curr_bowl, 1, i, 0)
                    
                if not st.session_state.userbatting or st.session_state.balls1 >= 30 or (st.session_state.target > 0 and st.session_state.l1 >= st.session_state.target):
                    if st.session_state.curr_bat in st.session_state.userbatting.values():
                        save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    st.session_state.curr_bowl = None
                    st.session_state.curr_bat = None 
                    st.session_state.last_over_balls = 0
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    
                    if st.session_state.phase == 'inning1_user_bat':
                        st.session_state.target = st.session_state.l1 + 1
                        st.session_state.phase = 'inning2_sys_bat'
                    else:
                        st.session_state.phase = 'match_over'
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
        # RANDOM OPPONENT BATSMAN LOGIC
        if st.session_state.curr_bat is None or st.session_state.curr_bat not in st.session_state.sysbatting.values():
            if st.session_state.sysbatting:
                st.session_state.curr_bat = r.choice(list(st.session_state.sysbatting.values()))
                st.session_state.show_stats = True # Show stats when new bot comes in
        if st.session_state.curr_bat:
            st.markdown(f"#### 🏏 Opponent Batsman: **{st.session_state.curr_bat}**")

    with col2:
        # Force user to pick a new bowler every over
        if st.session_state.curr_bowl is None or (st.session_state.balls2 > 0 and st.session_state.balls2 % 6 == 0 and st.session_state.last_over_balls != st.session_state.balls2):
            st.session_state.curr_bowl = None # Reset so they have to pick!
            st.session_state.last_over_balls = st.session_state.balls2
            st.toast("🔄 OVER COMPLETE! Pick your next bowler.", icon="🔄")
            
        st.session_state.curr_bowl = st.selectbox("Select your Bowler:", list(st.session_state.userbowling.values()), index=None, placeholder="Hand the ball to...")
        
        if st.session_state.curr_bowl != st.session_state.last_selected_bowl and st.session_state.curr_bowl is not None:
            st.session_state.show_stats = True
            st.session_state.last_selected_bowl = st.session_state.curr_bowl

    # Display Career Stats ONLY when show_stats is True
    if st.session_state.show_stats and st.session_state.curr_bat and st.session_state.curr_bowl:
        st.sidebar.header("📋 Pre-Delivery Stats")
        fetch_career_stats(st.session_state.curr_bat, "bat", False)
        fetch_career_stats(st.session_state.curr_bowl, "bowl", True)

    # Hide game buttons until a bowler is selected!
    if st.session_state.curr_bowl is None:
        st.warning("⚠️ Waiting for captain... Please select a Bowler to continue the over!")
    else:
        st.write("### Bowl your delivery:")
        cols = st.columns(6)
        for i in range(1, 7):
            if cols[i-1].button(str(i), key=f"bowl_{i}", use_container_width=True):
                st.session_state.show_stats = False # HIDE STATS IMMEDIATELY ON CLICK
                sys_bat = r.randint(1,6)
                st.session_state.balls2 += 1
                st.session_state.curr_bat_balls += 1
                
                if i == sys_bat:
                    st.toast("WICKET!!!", icon="🚨")
                    st.error(f"🚨 **GOT HIM!** Opponent played {sys_bat}. **{st.session_state.curr_bat}** is OUT!")
                    
                    st.session_state.wickets2 += 1
                    update_bowling('d11', st.session_state.curr_bowl, 1, 0, 1)
                    save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    st.session_state.sysbatting = {k:v for k,v in st.session_state.sysbatting.items() if v != st.session_state.curr_bat}
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    st.session_state.timeline2.append(st.session_state.l2)
                    st.session_state.curr_bat = None
                    
                else:
                    st.warning(f"Opponent played {sys_bat}. They scored **{sys_bat}** runs.")
                    st.session_state.l2 += sys_bat
                    st.session_state.curr_bat_runs += sys_bat
                    st.session_state.timeline2.append(st.session_state.l2)
                    update_bowling('d11', st.session_state.curr_bowl, 1, sys_bat, 0)
                    
                # Check for End of Innings
                if not st.session_state.sysbatting or st.session_state.balls2 >= 30 or (st.session_state.target > 0 and st.session_state.l2 >= st.session_state.target):
                    if st.session_state.curr_bat in st.session_state.sysbatting.values():
                        save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    
                    st.session_state.curr_bowl = None
                    st.session_state.curr_bat = None 
                    st.session_state.last_over_balls = 0
                    st.session_state.curr_bat_runs = 0
                    st.session_state.curr_bat_balls = 0
                    
                    if st.session_state.phase == 'inning1_sys_bat':
                        st.session_state.target = st.session_state.l2 + 1
                        st.session_state.phase = 'inning2_user_bat'
                    else:
                        st.session_state.phase = 'match_over'
                st.rerun()
