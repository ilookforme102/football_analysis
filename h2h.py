from openai import OpenAI
import openai
import time
import numpy as np
import json
import math
import pymysql
import os
import datetime

# Get API KEY
from dotenv import load_dotenv
import os
load_dotenv() 
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=api_key,
    )
def connect_to_database():
    # Modify with your database connection details
    return pymysql.connect(
        host='128.199.228.235', 
        user='sql_dabanhtructi', 
        password='FKb75AYJzFMJET8F', 
        database='sql_dabanhtructi',
        #connect_timeout=30000,
        port = 3306)
def get_datetime_obj():
    # Example Unix timestamp
    unix_timestamp_today = time.time() + 0*24*3600  # This is an example timestamp
    # Convert Unix timestamp to datetime object
    dt_object = datetime.datetime.fromtimestamp(unix_timestamp_today)
    # Format the datetime object as a string
    formatted_date_today = dt_object.strftime('%Y-%m-%d')
    return formatted_date_today
def get_matches(offset_number,conn,bulk):
    formatted_date_today = get_datetime_obj()
    # Create a cursor object
    cursor = conn.cursor()

    # Execute a query
    cursor.execute("""SELECT m.id, c.name as competition, v.name as stadium , v.city city, home_team.name home_team, away_team.name away_team, m.match_time match_time, h.h2h, h.home ,h.away, m.home_scores home_scores, m.away_scores away_scores 
    FROM `wpdbtt_api_matches` as m 
    LEFT JOIN `wpdbtt_api_competition` as c 
    ON m.competition_id = c.competition_id 
    LEFT JOIN `wpdbtt_api_venue` as v 
    ON m.venue_id = v.venue_id 
    JOIN (
        SELECT team_id, name, national, country_logo, logo
        FROM (
            SELECT team_id, name, national, country_logo, logo,
                    ROW_NUMBER() OVER (PARTITION BY team_id) AS rn
            FROM wpdbtt_api_team
            WHERE logo != ''
        ) AS ranked_teams
        WHERE rn = 1) AS home_team ON m.home_team_id = home_team.team_id 
    JOIN (
        SELECT team_id, name, national, country_logo, logo
        FROM (
            SELECT team_id, name, national, country_logo, logo,
                    ROW_NUMBER() OVER (PARTITION BY team_id) AS rn
            FROM wpdbtt_api_team
            WHERE logo != ''
        ) AS ranked_teams
        WHERE rn = 1) AS away_team ON m.away_team_id = away_team.team_id
    LEFT JOIN `wpdbtt_api_match_h2h` as h 
    ON m.id = h.match_id 
    WHERE DATE(FROM_UNIXTIME(m.match_time)) >= DATE(NOW()) AND DATE(FROM_UNIXTIME(m.match_time)) <= DATE(NOW() + INTERVAL 0 DAY)
    ORDER BY `m`.`match_time` DESC
    LIMIT {} OFFSET {}               
    """.format(bulk,offset_number))


    # Fetch all the rows in a list of lists.
    rows = cursor.fetchall()

    # Save all data to python dictionary
    match_dict = {}
    for index,row in enumerate(rows):
        item = {'match_id':row[0],
                'competition': row[1],
                'stadium':row[2],
                'city':row[3],
                'home_team':row[4],
                'away_team':row[5],
                'match_time':row[6],
                'h2h':row[7],
                'home':row[8],
                'away':row[9]
            }
        if row[8] is not None and row[9] is not None:
            match_dict[index] = item
            print("valid match",row[0])
        else:
            print("invalid match", row[0])
    return match_dict
def poisson_goal(g,eg):
    return (math.e**(-eg)*eg**g)/(math.factorial(g))
def get_match_info(match_data):
    try:
        team1 =  match_data['home_team']
        match_id = match_data['match_id']
        stadium = "sân vận động "+match_data['stadium'] if match_data['stadium'] != None else "sân nhà của " + match_data['home_team']
        team2 = match_data['away_team']
        league_name = match_data['competition']
        unix_time = match_data['match_time']
        list_days = {'Mon':'Thứ Hai','Tue':'Thứ Ba','Wed':'Thứ Tư','Thu':'Thứ Năm','Fri':'Thứ Sáu','Sat':'Thứ Bảy','Sun':'Chủ Nhật'}
        day_of_week_vi = list_days[time.strftime("%a", time.localtime(unix_time-0*3600))]
        date_dmy =time.strftime("%d/%m/%Y", time.localtime(unix_time-0*3600))
        time_hm= time.strftime("%H:%M", time.localtime(unix_time-0*3600))
        ########F
        
        ##home and away head2head stats
        #team1 as home 
        if match_data['h2h'] is not None:
            homeaway_h2h = json.loads(match_data['h2h'])[0]['matches']
            team1_h2h_home_scores = []
            for i in homeaway_h2h:
                if i['home_name']== team1:
                    team1_h2h_home_scores.append(i['home_scores'][0])
            #team2 as away
            team2_h2h_away_scores = []
            for i in homeaway_h2h:
                if i['away_name']== team2:
                    team2_h2h_away_scores.append(i['away_scores'][0]) 
        else:    
            team1_h2h_home_scores = [0]
            team2_h2h_away_scores = [0]
        #Avg team 1 h2h home scores 5 recent games
        team1_avg_h2h_home_scores = np.mean(team1_h2h_home_scores[0:5]) if len(team1_h2h_home_scores[0:5]) > 0 else 0
        #Avg team 2 h2h away score 5 recent games
        team2_avg_h2h_away_scores = np.mean(team2_h2h_away_scores[0:5]) if len(team2_h2h_away_scores[0:5]) > 0 else 0

        #H2H recents 5 games
        
        if match_data['h2h'] is not None:
            #homeaway_h2h = json.loads(match_data['h2h'])[0]['matches'][0:5]
            all_matches = [match for match in json.loads(match_data['h2h'])[0]['matches']]
            # Sort the matches by 'match_time'
            sorted_matches = sorted(all_matches, key=lambda x: x['match_time'],reverse=True)
            homeaway_h2h = sorted_matches[:5]
            team1_h2h_stats = {'win':0,'draw':0,'loss':0}
            for i in homeaway_h2h:
                if i['home_scores'][1] > i['away_scores'][1]:
                    if i['home_name'] == team1:
                        team1_h2h_stats['win']+=1
                    else:
                        team1_h2h_stats['loss']+=1
                elif i['home_scores'][1] == i['away_scores'][1]:
                    team1_h2h_stats['draw']+=1
                else:
                    if i['home_name'] == team1:
                        team1_h2h_stats['loss']+=1
                    else:
                        team1_h2h_stats['win']+=1
        else:
            team1_h2h_stats = {'win':0,'draw':0,'loss':0}
        #Team1 stats 5 recent games:
        home_stats = {'win':0,'draw':0,'loss':0}
        #homeaway_home  =  json.loads(match_data['home'])[0]['matches'][0:5]
        all_matches =  [match for match in json.loads(match_data['home'])[0]['matches']]
        # Sort the matches by 'match_time'
        sorted_matches = sorted(all_matches, key=lambda x: x['match_time'],reverse=True)
        homeaway_home = sorted_matches[:5]
        for i in homeaway_home:
            if i['home_scores'][1] > i['away_scores'][1]:
                if i['home_name'] == team1:
                    home_stats['win']+=1
                else:
                    home_stats['loss']+=1
            elif i['home_scores'][1] == i['away_scores'][1]:
                home_stats['draw']+=1
            else:
                if i['home_name'] == team1:
                    home_stats['loss']+=1
                else:
                    home_stats['win']+=1
        #Team2 stats 5 recent games
        away_stats = {'win':0,'draw':0,'loss':0}
        #homeaway_away =  json.loads(match_data['away'])[0]['matches'][0:5]
        all_matches =  [match for match in json.loads(match_data['away'])[0]['matches']]
        sorted_matches = sorted(all_matches, key=lambda x: x['match_time'],reverse=True)
        homeaway_away = sorted_matches[:5]
        for i in homeaway_away:
            if i['home_scores'][1] > i['away_scores'][1]:
                if i['home_name'] == team2:
                    away_stats['win']+=1
                else:
                    away_stats['loss']+=1
            elif i['home_scores'][1] == i['away_scores'][1]:
                away_stats['draw']+=1
            else:
                if i['home_name'] == team2:
                    away_stats['loss']+=1
                else:
                    away_stats['win']+=1
        #Team1 GA and GF scores
        #team1_home_ga_scores=[]
        team1_home_gf_scores=[]
        #homeaway_home = json.loads(match_data['home'])[0]['matches']
        all_matches =  [match for match in json.loads(match_data['home'])[0]['matches']]
        # Sort the matches by 'match_time'
        sorted_matches = sorted(all_matches, key=lambda x: x['match_time'],reverse=True)
        homeaway_home = sorted_matches[:]
        for i in homeaway_home:
            if i['home_name']== team1:
                #team1_home_ga_scores.append(i['home_scores'][0])
                team1_home_gf_scores.append(i['away_scores'][1])
        team1_avg_home_gf_scores = np.mean(team1_home_gf_scores) if len(team1_home_gf_scores) > 0 else 0
        team2_away_gf_scores=[]
        #homeaway_away = json.loads(match_data['away'])[0]['matches']
        all_matches =  [match for match in json.loads(match_data['away'])[0]['matches']]
        sorted_matches = sorted(all_matches, key=lambda x: x['match_time'],reverse=True)
        homeaway_away = sorted_matches[:]
        for i in homeaway_away:
            if i['away_name']== team2:
                team2_away_gf_scores.append(i['away_scores'][1])
                #team2_away_gf_scores.append(i['home_scores'][0])
        team2_avg_away_gf_scores = np.mean(team2_away_gf_scores) if len(team2_away_gf_scores) > 0 else 0
    
        #team1_home_eg_adjst_ratio = (team1_avg_h2h_home_scores + team1_avg_home_gf_scores)/2
        #team2_away_eg_adjst_ratio = (team2_avg_h2h_away_scores + team2_avg_away_gf_scores)/2
        #Home and Away EG
        home_eg = (team1_avg_h2h_home_scores + team1_avg_home_gf_scores)/2
        away_eg = (team2_avg_h2h_away_scores + team2_avg_away_gf_scores)/2
        
        #Home team goals probabilty, assume goals only in range 0-7
        home_goals_probs = []
        for i in range(0,8):
            prob = poisson_goal(i,home_eg)
            home_goals_probs.append(prob)
        #Away team goals probability, assume that goals are only in range 0-7
        away_goals_probs = []
        for i in range(0,8):
            prob = poisson_goal(i,away_eg)
            away_goals_probs.append(prob)
        #Home and Away goals prediction:
        home_goal_pred = home_goals_probs.index(max(home_goals_probs))
        away_goal_pred = away_goals_probs.index(max(away_goals_probs))
        #Probability that Home team win:
        home_win_prob_list = []
        for i in range(0,len(home_goals_probs)):
            for j in range(0,len(away_goals_probs)):
                if j < i:
                    home_win_prob_list.append(home_goals_probs[i]*away_goals_probs[j])
        home_win_prob = sum(home_win_prob_list)
        #Probability that both team draw:
        draw_prob = sum(np.array(home_goals_probs)*np.array(away_goals_probs))
        #Probability that Away team win:
        away_win_prob = 1 - draw_prob - home_win_prob
        #Probability that both team will score
        both_team_score_goal_list = []
        for i in home_goals_probs:
            both_team_score_goal_list.append(i*away_goals_probs[0])
        for j in away_goals_probs[1:]:
            both_team_score_goal_list.append(j*home_goals_probs[0])
        both_team_score_prob = 1 - sum(both_team_score_goal_list)
        return team1,team2,league_name,day_of_week_vi,date_dmy,time_hm,stadium,team1_h2h_stats,home_stats,away_stats,home_goal_pred,away_goal_pred,home_win_prob,away_win_prob,draw_prob,both_team_score_prob,home_goals_probs,away_goals_probs,match_id
    except TypeError as e:
        print(e) 
def write_content4turbo(team1,team2,league_name,day_of_week_vi,date_dmy,time_hm,stadium,team1_h2h_stats,home_stats,away_stats,home_goal_pred,away_goal_pred,home_win_prob,away_win_prob,draw_prob,both_team_score_prob):
        completion = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        temperature = 1.0,
        max_tokens = 2000,
        messages = [
            {"role": "system", "content": "bạn có am hiểu về phân tích và nhận định các trận bóng đá"}, 
            {"role": "system", "content": "Hãy nhấn mạnh rằng AI là người tạo ra các phân tích, nhận định và dự đoán về các tỷ lệ kèo này"}, 
            {"role": "system", "content": "Bạn chỉ đưa ra nhận định dựa trên những số liệu thống kê được cung cấp mà không sử dụng thêm thông tin bên ngoài."}, 
            {"role": "system", "content": f"""Các số liệu thống kê trước trận đấu giữa {team1} và {team2} được trình bày như sau:Trong 5 lần gặp nhau gần nhất giữa {team1} và {team2}, {team1} thắng {team1_h2h_stats['win']} thua {team1_h2h_stats['loss']} và hòa {team1_h2h_stats['draw']} 
    Trong 5 trận gần nhất của giải đấu {league_name}, {team1} thắng {home_stats['win']}, thua {home_stats['loss']} hòa {home_stats['draw']}.
    Trong 5 trận gần nhất của giải đấu {league_name} team {team2} thắng {away_stats['win']}, hòa {away_stats['draw']}, thua {away_stats['loss']}. 
    Đu tỉ số của trận đấu này sẽ là {home_goal_pred}-{away_goal_pred}. Xác suất thắng của {team1} là {np.round(100*home_win_prob,2)}%, xác suất thắng của team {team2} là {np.round(100*away_win_prob,2)}%, xác suất để 2 đội hòa nhau là {np.round(100*draw_prob,2)}% và xác suất để cả hai team cùng ghi bàn là {np.round(100*both_team_score_prob,2)}%. """}, 
            {"role": "user", "content": f"Dựa vào những thông tin trên, hãy viết một bài nhận định và dự đoán về trận đấu giữa chủ nhà {team1} và {team2} diễn ra vào {time_hm} ngày {day_of_week_vi}, {date_dmy} tại {stadium}"},         
            {"role": "user", "content": "Bài viết phải có sắc thái chuyên nghiệp, khách quan và có tính thuyết phục"},
            #{"role": "user", "content": "Bài viết phải sử dụng toàn bộ các thông tin đã được cung cấp "}
            ]
            
        )
        return completion.choices[0].message.content
#Get list of match_id for specific day    
def get_match_ids():
    # Database connection parameters - replace with your actual details
    formatted_date_today = get_datetime_obj()
    conn = connect_to_database()    
    try:
        with conn.cursor() as cursor:
            # SQL query
            sql = """
            SELECT `match_id` FROM `wpdbtt_api_analysis` a 
            LEFT JOIN `wpdbtt_api_matches` m ON a.match_id = m.id 
            WHERE DATE(FROM_UNIXTIME(m.match_time)) >= DATE(NOW()) AND DATE(FROM_UNIXTIME(m.match_time)) <= DATE(NOW() + INTERVAL 0 DAY);
            """

            # Execute the query
            cursor.execute(sql)

            # Fetch all the rows
            rows = cursor.fetchall()

            # Extract match_id from each row
            match_ids = [row[0] for row in rows]
            return match_ids

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        # Close the connection
        conn.close()
# Write new function call insert_prediction
def insert_prediction(current_offset_number,bulk):
    # Establish a database connection
    match_ids = get_match_ids()
    conn1 = connect_to_database()
    match_dict = get_matches(current_offset_number,conn1,bulk)
    conn1.close()
    for keys, values in match_dict.items():
        try:
            match_data = match_dict[keys]
            team1,team2,league_name,day_of_week_vi,date_dmy,time_hm,stadium,team1_h2h_stats,home_stats,away_stats,home_goal_pred,away_goal_pred,home_win_prob,away_win_prob,draw_prob,both_team_score_prob,home_goals_probs,away_goals_probs,match_id = get_match_info(match_data)
            
            analysis = "hahahaha"#write_content4turbo(team1,team2,league_name,day_of_week_vi,date_dmy,time_hm,stadium,team1_h2h_stats,home_stats,away_stats,home_goal_pred,away_goal_pred,home_win_prob,away_win_prob,draw_prob,both_team_score_prob)
            match_data['analysis'] = analysis
            print('Analysis for',keys,match_id,team1_h2h_stats,home_stats,away_stats, ' has been written')
        except Exception as e :
            print(e)
    # Create a cursor object
    
insert_prediction(0,10)