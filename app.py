import streamlit as st
import random as r
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime as dt

if 'phase' not in st.session_state:
    st.session_state.phase = 'toss'
    st.session_state.l1 = 0
    st.session_state.l2 = 0
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

def update_bowling(dict_name, bowler, balls, runs, wickets):
    if bowler not in st.session_state[dict_name]:
        st.session_state[dict_name][bowler] = [0, 0, 0, 0.0] # Overs, Runs, Wkts, Eco
    st.session_state[dict_name][bowler][0] += balls
    st.session_state[dict_name][bowler][1] += runs
    st.session_state[dict_name][bowler][2] += wickets

def save_batsman(dict_name, batsman, runs, balls):
    avg = runs // balls if balls > 0 else 0
    st.session_state[dict_name][batsman] = [runs, balls, avg]

st.title("🏏 India vs Australia")
st.write("="*50)

if st.session_state.phase == 'toss':
    st.header("The Toss")
    n = st.radio("Enter Even or Odd:", ["Even", "Odd"])
    num = st.number_input("Enter no between (1-10):", 1, 10)
    
    if st.button("Play Toss"):
        num1 = r.randint(1,10)
        total = num + num1
        st.write(f"Opponent chose: **{num1}**")
        
        is_even = (total % 2 == 0)
        user_won = (n == "Even" and is_even) or (n == "Odd" and not is_even)
        
        if user_won:
            st.success("You won the toss! You elected to Bat first.")
            st.session_state.user_bat_inning = 1
            st.session_state.phase = 'inning1_user_bat'
            st.rerun()
        else:
            st.error("You lost the toss! Opponent elected to Bat first.")
            st.session_state.user_bat_inning = 2
            st.session_state.phase = 'inning1_sys_bat'
            st.rerun()

elif st.session_state.phase in ['inning1_user_bat', 'inning2_user_bat']:
    st.header(f"You are Batting! (Score: {st.session_state.l1})")
    if st.session_state.target > 0:
        st.subheader(f"Target: {st.session_state.target}")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.curr_bat = st.selectbox("Select Batsman:", list(st.session_state.userbatting.values()))
    with col2:
        st.session_state.curr_bowl = r.choice(list(st.session_state.sysbowling.values()))
        st.write(f"Opponent Bowler: **{st.session_state.curr_bowl}**")

    st.write("### Play your shot:")
    cols = st.columns(6)
    for i in range(1, 7):
        if cols[i-1].button(str(i), key=f"bat_{i}"):
            sys_bowl = r.randint(1,6)
            st.session_state.balls1 += 1
            st.session_state.curr_bat_balls += 1
            
            if i == sys_bowl:
                st.error(f"Opponent bowled {sys_bowl}. WICKET!")
                update_bowling('d22', st.session_state.curr_bowl, 1, 0, 1)
                save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)

                st.session_state.userbatting = {k:v for k,v in st.session_state.userbatting.items() if v != st.session_state.curr_bat}
                st.session_state.curr_bat_runs = 0
                st.session_state.curr_bat_balls = 0
                st.session_state.timeline1.append(st.session_state.l1)
                
                if not st.session_state.userbatting or st.session_state.balls1 >= 30:
                    st.info("Innings Over!")
                    if st.session_state.phase == 'inning1_user_bat':
                        st.session_state.target = st.session_state.l1 + 1
                        st.session_state.phase = 'inning2_sys_bat'
                    else:
                        st.session_state.phase = 'match_over'
                st.rerun()
                
            else:
                st.success(f"Opponent bowled {sys_bowl}. You scored {i} runs!")
                st.session_state.l1 += i
                st.session_state.curr_bat_runs += i
                st.session_state.timeline1.append(st.session_state.l1)
                update_bowling('d22', st.session_state.curr_bowl, 1, i, 0)

                if st.session_state.target > 0 and st.session_state.l1 >= st.session_state.target:
                    save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    st.session_state.phase = 'match_over'
                elif st.session_state.balls1 >= 30:
                    save_batsman('d1', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    if st.session_state.phase == 'inning1_user_bat':
                        st.session_state.target = st.session_state.l1 + 1
                        st.session_state.phase = 'inning2_sys_bat'
                    else:
                        st.session_state.phase = 'match_over'
                st.rerun()

elif st.session_state.phase in ['inning1_sys_bat', 'inning2_sys_bat']:
    st.header(f"Opponent is Batting! (Score: {st.session_state.l2})")
    if st.session_state.target > 0:
        st.subheader(f"Target: {st.session_state.target}")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.curr_bowl = st.selectbox("Select your Bowler:", list(st.session_state.userbowling.values()))
    with col2:
        st.session_state.curr_bat = r.choice(list(st.session_state.sysbatting.values()))
        st.write(f"Opponent Batsman: **{st.session_state.curr_bat}**")

    st.write("### Bowl your delivery:")
    cols = st.columns(6)
    for i in range(1, 7):
        if cols[i-1].button(str(i), key=f"bowl_{i}"):
            sys_bat = r.randint(1,6)
            st.session_state.balls2 += 1
            st.session_state.curr_bat_balls += 1
            
            if i == sys_bat:
                st.success(f"Opponent played {sys_bat}. WICKET!")
                update_bowling('d11', st.session_state.curr_bowl, 1, 0, 1)
                save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                
                st.session_state.sysbatting = {k:v for k,v in st.session_state.sysbatting.items() if v != st.session_state.curr_bat}
                st.session_state.curr_bat_runs = 0
                st.session_state.curr_bat_balls = 0
                st.session_state.timeline2.append(st.session_state.l2)
                
                if not st.session_state.sysbatting or st.session_state.balls2 >= 30:
                    st.info("Innings Over!")
                    if st.session_state.phase == 'inning1_sys_bat':
                        st.session_state.target = st.session_state.l2 + 1
                        st.session_state.phase = 'inning2_user_bat'
                    else:
                        st.session_state.phase = 'match_over'
                st.rerun()
                
            else:
                st.error(f"Opponent played {sys_bat}. They scored {sys_bat} runs.")
                st.session_state.l2 += sys_bat
                st.session_state.curr_bat_runs += sys_bat
                st.session_state.timeline2.append(st.session_state.l2)
                update_bowling('d11', st.session_state.curr_bowl, 1, sys_bat, 0)
                
                if st.session_state.target > 0 and st.session_state.l2 >= st.session_state.target:
                    save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    st.session_state.phase = 'match_over'
                elif st.session_state.balls2 >= 30:
                    save_batsman('d2', st.session_state.curr_bat, st.session_state.curr_bat_runs, st.session_state.curr_bat_balls)
                    if st.session_state.phase == 'inning1_sys_bat':
                        st.session_state.target = st.session_state.l2 + 1
                        st.session_state.phase = 'inning2_user_bat'
                    else:
                        st.session_state.phase = 'match_over'
                st.rerun()

elif st.session_state.phase == 'match_over':
    st.header("MATCH FINISHED")
    
    if st.session_state.l1 > st.session_state.l2:
        st.success("🏆 You won the match!!")
    elif st.session_state.l2 > st.session_state.l1:
        st.error("💀 You lose.")
    else:
        st.info("🤝 Draw.")

    for d in [st.session_state.d11, st.session_state.d22]:
        for k in d:
            overs = d[k][0] / 6
            d[k][0] = overs
            d[k][3] = d[k][1] / overs if overs > 0 else 0

    st.subheader("Your Batting")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.d1, orient='index', columns=['Runs', 'Balls', 'Avg']))
    
    st.subheader("Match Graph")
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(st.session_state.timeline1)), st.session_state.timeline1, label='You', marker='o')
    plt.plot(range(len(st.session_state.timeline2)), st.session_state.timeline2, label='Opponent', linestyle='--', marker='x')
    plt.title("Run Chase Analysis")
    plt.legend()
    st.pyplot(plt.gcf())
    
    if st.button("Save Stats to Database"):
        payload = {
            "d1": st.session_state.d1, "d11": st.session_state.d11,
            "d2": st.session_state.d2, "d22": st.session_state.d22
        }
        try:
            res = requests.post("https://cricket-api-backend-3zph.onrender.com/save_match", json=payload)
            st.success(res.json().get("message", "Saved!"))
        except:
            st.error("Failed to connect to Flask API.")

            