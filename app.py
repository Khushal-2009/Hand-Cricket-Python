import streamlit as st
import random as r
import pandas as pd
from plotly import graph_objects as go
import requests
import datetime as dt

# --- API CONFIGURATION ---
# CHANGE THIS TO YOUR ACTUAL RENDER URL!
API_URL = "https://YOUR-RENDER-API-URL.onrender.com" 

# --- 1. SETUP MEMORY (SESSION STATE) ---
if 'phase' not in st.session_state:
    st.session_state.phase = 'toss'
    st.session_state.l1 = 0 # User Runs
    st.session_state.l2 = 0 # Sys Runs
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
    
    st.session_state.userbatting = {1:"Virat Kohli",2:"Rohit Sharma",3:"Dhoni",4:"Hardik",5:"Jadeja"}
    st.session_state.userbowling = {1:"Bumrah",2:"Chahal",3:"Siraj",4:"Kuldeep",5:"Hardik"}
    st.session_state.sysbatting = {1:'Travis Head',2:'Steve Smith',3:'Mitchell Marsh',4:'Cameron Green',5:'Josh Inglis'}
    st.session_state.sysbowling = {1:'Pat Cummins',2:'Mitchell Starc',3:'Josh Hazlewood',4:'Nathan Lyon',5:'Adam Zampa'}
    
    st.session_state.curr_bat = None
    st.session_state.curr_bowl = None
    st.session_state.curr_bat_runs = 0
    st.session_state.curr_bat_balls = 0
    st.session_state.last_over_balls = 0

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
            st.sidebar.markdown(f"### 📊 {player_name.upper()} Career")
            for key, value in stats.items():
                st.sidebar.write(f"**{key}:** {value}")
        else:
            st.sidebar.info("Debut match! No prior stats found.")
    except:
        pass # Silently fail if API is asleep

# --- UI: MAIN BANNER ---
st.set_page_config(page_title="Khushal's Hand Cricket", page_icon="🏏", layout="centered")
st.title("🏏 INDIA VS AUSTRALIA")
st.write("---")

# --- PHASE: TOSS ---
if st.session_state.phase == 'toss':
    st.header("The Toss")
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
    
    # Dynamic Scoreboard
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
        st.session_state.curr_bat = st.selectbox("Select Batsman:", list(st.session_state.userbatting.values()))
        fetch_career_stats(st.session_state.curr_bat, "bat", True)
    with col2:
        # Bowler Logic: Change only at start or after an over
        if st.session_state.curr_bowl is None or (st.session_state.balls1 > 0 and st.session_state.balls1 % 6 == 0 and st.session_state.last_over_balls != st.session_state.balls1):
            st.session_state.curr_bowl = r.choice(list(st.session_state.sysbowling.values()))
            st.session_state.last_over_balls = st.session_state.balls1
            st.toast(f"🥎 New Over! {st.session_state.curr_bowl} comes into the attack.")
        st.info(f"🥎 **Bowler:** {st.session_state.curr_bowl}")

    st.write("### Play your shot:")
    cols = st.columns(6)
    for i in range(1, 7):
        if cols[i-1].button(str(i), key=f"bat_{i}", use_container_width=True):
            sys_bowl = r.randint(1,6)
            st.session_state.balls1 += 1
            st.session_state.curr_bat_balls += 1
            
            if i == sys_bowl:
                st.error(f"Opponent bowled {sys_bowl}. OUT!")
                st.session_state.wickets1 += 1
                update_bowling('d22', st.session_state.curr_bowl, 1, 0, 1)
                save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                
                st.session_state.userbatting = {k:v for k,v in st.session_state.userbatting.items() if v != st.session_state.curr_bat}
                st.session_state.curr_bat_runs = 0
                st.session_state.curr_bat_balls = 0
                st.session_state.timeline1.append(st.session_state.l1)
                
            else:
                st.success(f"Opponent bowled {sys_bowl}. You scored {i} runs!")
                st.session_state.l1 += i
                st.session_state.curr_bat_runs += i
                st.session_state.timeline1.append(st.session_state.l1)
                update_bowling('d22', st.session_state.curr_bowl, 1, i, 0)
                
            # Check for End of Innings
            if not st.session_state.userbatting or st.session_state.balls1 >= 30 or (st.session_state.target > 0 and st.session_state.l1 >= st.session_state.target):
                if st.session_state.curr_bat in st.session_state.userbatting.values():
                    save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                
                st.session_state.curr_bowl = None
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
        st.session_state.curr_bat = st.selectbox("Select Opponent Batsman:", list(st.session_state.sysbatting.values()))
    with col2:
        if st.session_state.curr_bowl is None or (st.session_state.balls2 > 0 and st.session_state.balls2 % 6 == 0 and st.session_state.last_over_balls != st.session_state.balls2):
            st.session_state.last_over_balls = st.session_state.balls2
            st.toast("🥎 End of Over! Pick your next bowler.")
        st.session_state.curr_bowl = st.selectbox("Select your Bowler:", list(st.session_state.userbowling.values()))
        fetch_career_stats(st.session_state.curr_bowl, "bowl", True)

    st.write("### Bowl your delivery:")
    cols = st.columns(6)
    for i in range(1, 7):
        if cols[i-1].button(str(i), key=f"bowl_{i}", use_container_width=True):
            sys_bat = r.randint(1,6)
            st.session_state.balls2 += 1
            st.session_state.curr_bat_balls += 1
            
            if i == sys_bat:
                st.success(f"Opponent played {sys_bat}. WICKET!")
                st.session_state.wickets2 += 1
                update_bowling('d11', st.session_state.curr_bowl, 1, 0, 1)
                save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                
                st.session_state.sysbatting = {k:v for k,v in st.session_state.sysbatting.items() if v != st.session_state.curr_bat}
                st.session_state.curr_bat_runs = 0
                st.session_state.curr_bat_balls = 0
                st.session_state.timeline2.append(st.session_state.l2)
                
            else:
                st.error(f"Opponent played {sys_bat}. They scored {sys_bat} runs.")
                st.session_state.l2 += sys_bat
                st.session_state.curr_bat_runs += sys_bat
                st.session_state.timeline2.append(st.session_state.l2)
                update_bowling('d11', st.session_state.curr_bowl, 1, sys_bat, 0)
                
            # Check for End of Innings
            if not st.session_state.sysbatting or st.session_state.balls2 >= 30 or (st.session_state.target > 0 and st.session_state.l2 >= st.session_state.target):
                if st.session_state.curr_bat in st.session_state.sysbatting.values():
                    save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                
                st.session_state.curr_bowl = None
                st.session_state.last_over_balls = 0
                st.session_state.curr_bat_runs = 0
                st.session_state.curr_bat_balls = 0
                
                if st.session_state.phase == 'inning1_sys_bat':
                    st.session_state.target = st.session_state.l2 + 1
                    st.session_state.phase = 'inning2_user_bat'
                else:
                    st.session_state.phase = 'match_over'
            st.rerun()

# --- PHASE: MATCH OVER ---
elif st.session_state.phase == 'match_over':
    st.header("🏆 MATCH FINISHED")
    
    if st.session_state.l1 > st.session_state.l2:
        st.success(f"India won by {st.session_state.l1 - st.session_state.l2} runs!")
    elif st.session_state.l2 > st.session_state.l1:
        st.error(f"Australia won by {5 - st.session_state.wickets2} wickets!")
    else:
        st.info("The match is a Draw!")

    # Format Bowling Stats
    for d in [st.session_state.d11, st.session_state.d22]:
        for k in d:
            overs = round(d[k][0] / 6, 1)
            d[k][0] = overs
            d[k][3] = round(d[k][1] / overs, 2) if overs > 0 else 0.00

    # Beautiful Dataframes
    st.subheader("🏏 India Batting Card")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.d1, orient='index', columns=['Runs', 'Balls', 'Strike Rate (%)']), use_container_width=True)
    
    st.subheader("🥎 Australia Bowling Card")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.d22, orient='index', columns=['Overs', 'Runs', 'Wickets', 'Economy']), use_container_width=True)

    # Interactive Plotly Graph!
    st.subheader("📈 Run Chase Flow")
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.timeline1, mode='lines+markers', name='India', line=dict(color='#1f77b4', width=3)))
    fig.add_trace(go.Scatter(y=st.session_state.timeline2, mode='lines+markers', name='Australia', line=dict(color='#ff7f0e', width=3, dash='dash')))
    fig.update_layout(xaxis_title="Balls Bowled", yaxis_title="Runs Scored", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    if st.button("💾 Save Match Stats to Cloud", use_container_width=True):
        payload = {"d1": st.session_state.d1, "d11": st.session_state.d11, "d2": st.session_state.d2, "d22": st.session_state.d22}
        with st.spinner("Connecting to Aiven Database via Flask..."):
            try:
                res = requests.post(f"{API_URL}/save_match", json=payload)
                st.success(res.json().get("message", "Data Successfully Saved!"))
            except:
                st.error("Failed to connect to the Server. Ensure Render API is awake.")
