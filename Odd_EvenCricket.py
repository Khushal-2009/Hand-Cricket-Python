import random as r
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
import mysql.connector as m
from mysql.connector import Error
import datetime as dt
load_dotenv()

def broadcast_stats(player_name, role, is_user):
    if role == "bat":
        table = 'user_batsmen' if is_user else 'sys_batsmen'
    else:
        table = 'user_bowler' if is_user else 'sys_bowler'
    
    try:
        conn = m.connect(
            host = 'mysql-21b750df-krishania63-f910.i.aivencloud.com',
            port = "22054",
            user = "avnadmin",
            password =os.getenv("AIVEN_PASSWORD"),
            database = "defaultdb"
        )
        
        cursor = conn.cursor()

        if role == 'bat':

            query = f'''
                SELECT
                    COUNT(*) as Matches,
                    SUM(Runs) as Total_Runs,
                    Max(Runs) as Highest_Score,
                    ROUND((SUM(Runs)/NULLIF (SUM(Balls_Played),0)) * 100, 2) as strike_Rate
                FROM {table}
                WHERE Name = '{player_name}';
                '''
        else:

            query = f''' 
                SELECT 
                    COUNT(*) as Matches,
                    SUM(Wickets) as Wickets,
                    SUM(Overs) as Overs,
                    ROUND((SUM(Runs))/ NULLIF (SUM(Overs),0), 2) as Economy
                FROM {table}
                WHERE Name = '{player_name}';
                '''  
        cursor.execute(query)
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]
        df = pd.DataFrame(data, columns=column_names)

        print(f"\n {player_name.upper()} CAREER STATS")  

        if df['Matches'][0] > 0 :
            df = df.fillna(0)
            print(df.to_string(index=False))
        else:
            print("DEBUT MATCH! No previous records.")

        print("_" * 40 + "\n")

    except Error as e:
        print(f'Database Error:{e}')

    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def graph():
    plt.figure(figsize=(10, 6))

    x1 = range(len(timeline1))
    x2 = range(len(timeline2))

    plt.plot(x1, timeline1, label='You (User)', color='#1f77b4', linewidth=2, marker='o', markersize=4, markevery=6)

    plt.plot(x2, timeline2, label='Opponent (System)', color='#ff7f0e', linewidth=2, linestyle='--', marker='x', markersize=4, markevery=6)
    
    wicket_x1 = []
    wicket_y1 = []
    for i in range(1, len(timeline1)):
        if timeline1[i] == timeline1[i-1]:
            wicket_x1.append(i)
            wicket_y1.append(timeline1[i])

    wicket_x2 = []
    wicket_y2 = []
    for i in range(1, len(timeline2)):
        if timeline2[i] == timeline2[i-1]:
            wicket_x2.append(i)
            wicket_y2.append(timeline2[i])

    if wicket_x1:
        plt.scatter(wicket_x1, wicket_y1, color='red', marker='X', s=50, zorder=5, label='User Wicket')
    if wicket_x2:
        plt.scatter(wicket_x2, wicket_y2, color='black', marker='X', s=50, zorder=5, label='Opp Wicket')

    max_balls = max(len(timeline1),len(timeline2))
    plt.xticks(range(0,max_balls+2,6))

    if user_bat_inning == 1:
        match_title = "Match Analysis: You Defending vs Opponent Chasing"
    else:
        match_title = "Match Analysis: Opponent Defending vs You Chasing"
        
    plt.title(match_title, fontsize=14, fontweight='bold')
    plt.xlabel('Balls Bowled', fontsize=12)
    plt.ylabel('Runs Scored', fontsize=12)

    if timeline1:
        plt.text(len(timeline1)-1, timeline1[-1], f" You: {timeline1[-1]}", 
                fontsize=10, color='#1f77b4', fontweight='bold', va='bottom')
    if timeline2:
        plt.text(len(timeline2)-1, timeline2[-1], f" Opp: {timeline2[-1]}", 
                fontsize=10, color='#ff7f0e', fontweight='bold', va='bottom')

    plt.legend(fontsize=11, loc='best')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    folder_name = "MatchGraphs"
    os.makedirs(folder_name,exist_ok=True)
    aq = dt.datetime.now()
    pq = aq.strftime("%d-%m-%Y_%H-%M")
    file_name = f"{pq}.png"
    full_save_path = os.path.join(folder_name,file_name)
    plt.savefig(full_save_path,dpi=300,facecolor='white',transparent=False)
    print(f'\n Match Graph saved successfully in :{folder_name}/{file_name}')
    plt.show()

l1 = 0
l2 = 0
timeline1 = [0]  
timeline2 = [0]
d1 = {}
d11 = {}
d2 = {}
d22 = {}
user_bat_inning = 0
aa = 0
a7=0
userbatting = {1:"Virat Kohli",2:"Rohit Sharma",3:"Dhoni",4:"Hardik",5:"Jadeja"}
userbowling = {1:"Bumrah",2:"Chahal",3:"Siraj",4:"Kuldeep",5:"Hardik"}
sysbatting = {1:'Travis Head',2:'Steve Smith',3:'Mitchell Marsh',4:'Cameron Green',5:'Josh Inglis'}
sysbowling = {1:'Pat Cummins',2:'Mitchell Starc',3:'Josh Hazlewood',4:'Nathan Lyon',5:'Adam Zampa'}

def update_bowling_stats(stats_dict, bowler_name, balls, runs, wickets):
    if bowler_name not in stats_dict:
        stats_dict[bowler_name] = [0, 0, 0]

    stats_dict[bowler_name][0] += balls    
    stats_dict[bowler_name][1] += runs     
    stats_dict[bowler_name][2] += wickets  
            
def userbattinglineup(outplayer=0):
    global aa
    global userbatting
    if outplayer in userbatting:
        outplayer = userbatting.pop(outplayer)
    if userbatting == {}:
        return
    print(userbatting)
    while True:
        try:
            aa = int(input("Enter player no.:"))
            if aa in userbatting:
                print(userbatting[aa],"selected")
                broadcast_stats(userbatting[aa], role = 'bat', is_user=True)
                break
            else:
                print("wrong option!!")
        except ValueError:
            print("Try again!!")

def userbowlinglineup():
    global userbowling
    global a7
    print(userbowling)
    while True:
        try:
            a7 = int(input("Enter player no.:"))
            if a7 in [1,2,3,4,5]:
                print(userbowling[a7],"selected")
                broadcast_stats(userbowling[a7], role='bowl', is_user=True)
                break
            else:
                print("wrong option!!")
        except ValueError:
            print("Try Again!!")

def sysbattinglineup(outplayer=0):
    global aa
    global sysbatting
    if outplayer in sysbatting:
        outplayer = sysbatting.pop(outplayer)
    if sysbatting == {}:
        return
    aa = r.choice(list(sysbatting.keys()))
    print("Opponent Selected",sysbatting[aa])
    broadcast_stats(sysbatting[aa], role='bat', is_user=False)
   
def sysbowlinglineup():
    global a7
    global sysbowling
    a7 = r.randint(1,5)
    print("Opponent Selected",sysbowling[a7])
    broadcast_stats(sysbowling[a7], role='bowl', is_user=False)
    
#1st Inning 
def firstinning(target=0):
    ballsplayed1 = 0
    l = []
    global l1
    global timeline1
    global d22
    global d1
    global aa
    global a7
    userbattinglineup()
    for x in range(1,6):
        if userbatting == {}:
            print("All OUT!!!")
            break
        print(x,'over')
        sysbowlinglineup()
        for y in range(1,7):
            a = int(input("Choose a no. between 1 and 6:"))
            if (a>0 and a<7):
                b = r.randint(1,6)
                print('opponent choose',b)
                if (a == b):
                    l.append(0)
                    print("Out")
                    timeline1.append(l1)
                    update_bowling_stats(d22,sysbowling[a7],1,0,1)
                    ballsplayed1+=1
                    g = sum(l)
                    avg = g // ballsplayed1 if ballsplayed1 > 0 else 0
                    d1[userbatting[aa]] = [g,ballsplayed1,avg]
                    ballsplayed1 = 0
                    l.clear()
                    userbattinglineup(outplayer = aa)
                    if userbatting == {}:
                        print("ALL OUT!!!")
                        return
                else:
                    l.append(a)
                    ballsplayed1+=1
                    l1+=a
                    timeline1.append(l1)
                    update_bowling_stats(d22,sysbowling[a7],1,a,0)
                    if target > 0 and l1 >= target:
                        print("Chase Completed!")  
                        g = sum(l)
                        avg = g // ballsplayed1 if ballsplayed1 > 0 else 0
                        d1[userbatting[aa]] = [g,ballsplayed1,avg]
                        return
            else:
                print("wrong choice!!")
    g = sum(l)
    avg = g // ballsplayed1 if ballsplayed1 > 0 else 0
    d1[userbatting[aa]] = [g,ballsplayed1,avg]
    
# 2nd Inning
def secondinning(target=0):
    ballsplayed2 = 0
    l = []
    global l2
    global timeline2
    global d2
    global d11
    global aa
    global a7
    sysbattinglineup()
    for x in range(1,6):
        if sysbatting == {}:
            print("ALL OUT!!!")
            break
        print(x,'Over')
        userbowlinglineup()
        for y in range(1,7):
            a = r.randint(1,6)
            b = int(input("Choose a no. between 1 and 6:"))
            if (b>0 and b<7):
                print('opponent choose',a)
                if (a==b):
                    l.append(0)
                    print("Wicket down!!")
                    timeline2.append(l2)
                    update_bowling_stats(d11,userbowling[a7],1,0,1)
                    ballsplayed2+=1
                    g = sum(l)
                    avg = g // ballsplayed2 if ballsplayed2 > 0 else 0
                    d2[sysbatting[aa]] = [g,ballsplayed2,avg]
                    ballsplayed2 = 0
                    l.clear()
                    sysbattinglineup(outplayer = aa)
                    if sysbatting == {}:
                        print("ALL OUT!!!")
                        return
                else:
                    l.append(a)
                    ballsplayed2+=1
                    l2+=a
                    timeline2.append(l2)
                    update_bowling_stats(d11,userbowling[a7],1,a,0)
                    if target > 0 and l2 >= target:
                        print("Chase Completed!")
                        g = sum(l)
                        avg = g // ballsplayed2 if ballsplayed2 > 0 else 0
                        d2[sysbatting[aa]] = [g,ballsplayed2,avg]
                        return
                    g = sum(l)
                    avg = g // ballsplayed2 if ballsplayed2 > 0 else 0
                    d2[sysbatting[aa]] = [g,ballsplayed2,avg]
            else:
                print("Wrong choice!!")
    
#TOSS

q = 0
def Toss(n,num):
    global l1
    global l2
    global user_bat_inning
    if n.capitalize() in ["Even","Odd"]:
        if n.capitalize() == "Even": 
            if (num>0 and num<=10):
                num1 = r.randint(1,10)
                print('opponent choose:',num1)
                if (num + num1)%2==0:
                    print("you won!!")
                    q = input("choose bat or ball:")
                    if q == 'bat': 
                        user_bat_inning = 1
                        firstinning()
                        print("2nd Inning")
                        print("Target:",l1 + 1)
                        secondinning(l1 + 1)

                    elif q == 'ball':
                        user_bat_inning = 2
                        secondinning()
                        print("2nd Inning")
                        print("Target:",l2+1)
                        firstinning(l2 + 1)
                else:
                    print("You lose!!")
                    l = ['bat','ball']
                    y = r.choice(l)
                    if y == 'bat':
                        print('opponent choose bat') 
                        user_bat_inning = 2
                        secondinning()
                        print("2nd Inning")
                        print("Target:",l2+1)
                        firstinning(l2 + 1)
                    else:
                        print('opponent choose ball') 
                        user_bat_inning = 1
                        firstinning()
                        print("2nd Inning")
                        print("Target:",l1+1)
                        secondinning(l1 + 1)
        else:
            if (num>0 and num<=10):
                num1 = r.randint(1,10)
                print('opponent choose:',num1)
                if (num + num1)%2 != 0:
                    print("you won!!")
                    q = input("choose bat or ball:")
                    if q == 'bat': 
                        user_bat_inning = 1
                        firstinning()
                        print("2nd Inning")
                        print("Target:",l1+1)
                        secondinning(l1 + 1)
                    elif q == 'ball': 
                        user_bat_inning = 2
                        secondinning()
                        print("2nd Inning")
                        print("Target:",l2+1)
                        firstinning(l2 + 1)
                else:
                    print("you loose!!")
                    l = ['bat','ball']
                    y = r.choice(l)
                    if y == 'bat': 
                        user_bat_inning = 2
                        print('opponent choose bat')
                        secondinning()
                        print("2nd Inning")
                        print("Target:",l2+1)
                        firstinning(l2 + 1)
                    else:
                        print('opponent choose ball') 
                        user_bat_inning = 1
                        firstinning()
                        print("2nd Inning")
                        print("Target:",l1+1)
                        secondinning(l1 + 1)
    
print("\n" + "="*50)
print(f"{'WELCOME! INDIA VS AUSTRALIA':^50}")
print("="*50)
print()
# Toss
print('Toss')
n=input('Enter even or odd:')
num=int(input('Enter no between(1-10):'))

Toss(n,num)

# Scorecard
def scorecard():
    print("\n" + "="*50)
    print(f"{'MATCH SCORECARD':^50}")
    print("="*50)

    def print_inning(team_name, batting_data, bowling_data, total_score):
        print(f"\n{team_name} Innings (Total: {total_score})")
        print("-" * 50)
        
        if batting_data:
            df_bat = pd.DataFrame.from_dict(batting_data, orient='index', columns=['Runs', 'Balls', 'Avg'])
            df_bat.index.name = 'Batsman'
            print(df_bat.to_string())
        else:
            print("No batting data.")

        print("-" * 50)
        
        if bowling_data:
            df_bowl = pd.DataFrame.from_dict(bowling_data, orient='index', columns=['Overs', 'Runs', 'Wkts', 'Eco'])
            df_bowl.index.name = 'Bowler'
            
            df_bowl['Overs'] = df_bowl['Overs'].map('{:.1f}'.format)
            df_bowl['Eco'] = df_bowl['Eco'].map('{:.2f}'.format)
            
            print(df_bowl.to_string())
        else:
            print("No bowling data.")
            
        print("=" * 50)

    if user_bat_inning == 1:
        print_inning("USER (1st Inn)", d1, d22, l1)
        print_inning("SYSTEM (2nd Inn)", d2, d11, l2)
    else:
        print_inning("SYSTEM (1st Inn)", d2, d11, l2)
        print_inning("USER (2nd Inn)", d1, d22, l1)

def database():
    global d1
    global d11
    global d2
    global d22
    date = dt.date.today()
    a = None
    b = None
    try:
        a = m.connect(
            host = "mysql-21b750df-krishania63-f910.i.aivencloud.com",
            port = "22054",
            user = "avnadmin",
            password =os.getenv("AIVEN_PASSWORD"),
            database = "defaultdb"
        )

        b = a.cursor()
        for x in d1:
            c = '''INSERT INTO user_batsmen VALUES(%s,%s,%s,%s,%s)'''
            d = (x,date,d1[x][0],d1[x][1],d1[x][2])
            b.execute(c,d)
        for x in d11:
            c = '''INSERT INTO user_bowler VALUES(%s,%s,%s,%s,%s,%s)'''
            d = (x,date,d11[x][0],d11[x][1],d11[x][2],d11[x][3])
            b.execute(c,d)
        for x in d2:
            c = '''INSERT INTO sys_batsmen VALUES(%s,%s,%s,%s,%s)'''
            d = (x,date,d2[x][0],d2[x][1],d2[x][2])
            b.execute(c,d)
        for x in d22:
            c = '''INSERT INTO sys_bowler VALUES(%s,%s,%s,%s,%s,%s)'''
            d = (x,date,d22[x][0],d22[x][1],d22[x][2],d22[x][3])
            b.execute(c,d)
        
        a.commit()
    except Error as e:
        print(f"Error while connecting to database: {e}")
    finally:
        if b:
            b.close()
        if a and a.is_connected():
            a.close()

for x in d11:
    aq = d11[x][0]
    bq = aq/6
    d11[x][0] = bq
    pq = d11[x][1]/d11[x][0]
    d11[x].append(pq)

for x in d22:
    aq = d22[x][0]
    bq = aq/6
    d22[x][0] = bq
    pq = d22[x][1]/d22[x][0]
    d22[x].append(pq)

scorecard()

#Result

my_score = l1
opp_score = l2

database()

if my_score > opp_score:
    print("You won the match!!")
elif opp_score > my_score:
    print("You lose")
elif my_score == opp_score:
    print("Draw")

graph()

