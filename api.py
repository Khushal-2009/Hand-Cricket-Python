from flask import Flask, request, jsonify
import mysql.connector
import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host='mysql-21b750df-krishania63-f910.i.aivencloud.com',
        port="22054",
        user="avnadmin",
        password=os.getenv("AIVEN_PASSWORD"), 
        database="defaultdb"
    )

@app.route('/save_match', methods=['POST'])
def save_match():
    data = request.json
    d1 = data.get('d1', {})
    d11 = data.get('d11', {})
    d2 = data.get('d2', {})
    d22 = data.get('d22', {})

    date = dt.date.today()

    try:
        conn = get_db_connection()
        b = conn.cursor()

        for x in d1:
            b.execute('''INSERT INTO user_batsmen VALUES(%s,%s,%s,%s,%s)''', (x, date, d1[x][0], d1[x][1], d1[x][2]))
        for x in d11:
            b.execute('''INSERT INTO user_bowler VALUES(%s,%s,%s,%s,%s,%s)''', (x, date, d11[x][0], d11[x][1], d11[x][2], d11[x][3]))
        for x in d2:
            b.execute('''INSERT INTO sys_batsmen VALUES(%s,%s,%s,%s,%s)''', (x, date, d2[x][0], d2[x][1], d2[x][2]))
        for x in d22:
            b.execute('''INSERT INTO sys_bowler VALUES(%s,%s,%s,%s,%s,%s)''', (x, date, d22[x][0], d22[x][1], d22[x][2], d22[x][3]))

        conn.commit()
        return jsonify({"status": "Success", "message": "Match data saved to Aiven!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            b.close()
            conn.close()

@app.route('/get_stats', methods=['POST'])
def get_stats():
    data = request.json
    player_name = data.get('player_name')
    role = data.get('role')
    is_user = data.get('is_user')

    if role == "bat":
        table = 'user_batsmen' if is_user else 'sys_batsmen'
    else:
        table = 'user_bowler' if is_user else 'sys_bowler'

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # dictionary=True makes it easy to send over the web

        if role == 'bat':
            query = f"SELECT COUNT(*) as Matches, SUM(Runs) as Total_Runs, Max(Runs) as Highest_Score, ROUND((SUM(Runs)/NULLIF (SUM(Balls_Played),0)) * 100, 2) as strike_Rate FROM {table} WHERE Name = '{player_name}';"
        else:
            query = f"SELECT COUNT(*) as Matches, SUM(Wickets) as Wickets, SUM(Overs) as Overs, ROUND((SUM(Runs))/ NULLIF (SUM(Overs),0), 2) as Economy FROM {table} WHERE Name = '{player_name}';"

        cursor.execute(query)
        stats = cursor.fetchall()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)


    