"""from openai import OpenAI
import openai
import time
import numpy as np
import json
import math
import pymysql
import os
import datetime
def connect_to_database():
    # Modify with your database connection details
    return pymysql.connect(
        host='128.199.228.235', 
        user='sql_dabanhtructi', 
        password='FKb75AYJzFMJET8F', 
        database='sql_dabanhtructi',
        #connect_timeout=30000,
        port = 3306)

def count_matches():
    # Example Unix timestamp
    unix_timestamp_today = time.time() + 0*24*3600  # This is an example timestamp
    # Convert Unix timestamp to datetime object
    dt_object = datetime.datetime.fromtimestamp(unix_timestamp_today)
    # Format the datetime object as a string
    formatted_date_today = dt_object.strftime('%Y-%m-%d')
    conn = connect_to_database()
    try:
        # Create a cursor object
        cursor = conn.cursor()

        # SQL query
        sql = "SELECT COUNT(*) as match_number FROM `wpdbtt_api_matches` WHERE FROM_UNIXTIME(`match_time`, '%Y-%m-%d') = '2023-12-22'"

        # Execute the query
        cursor.execute(sql)

        # Fetch the result
        result = cursor.fetchone()
        if result:
            return result[0]  # The first element of the result is match_number

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
t = count_matches()
print(t)"""
import openai
import time
import numpy as np
import json
import math
import pymysql
import os
import datetime
def connect_to_database():
    # Modify with your database connection details
    return pymysql.connect(
        host='128.199.228.235', 
        user='sql_dabanhtructi', 
        password='FKb75AYJzFMJET8F', 
        database='sql_dabanhtructi',
        #connect_timeout=30000,
        port = 3306)
conn = connect_to_database()
def get_matches(offset_number,conn,bulk):
    # Example Unix timestamp
    unix_timestamp_today = time.time() + 0*24*3600  # This is an example timestamp
    # Convert Unix timestamp to datetime object
    dt_object = datetime.datetime.fromtimestamp(unix_timestamp_today)
    # Format the datetime object as a string
    formatted_date_today = dt_object.strftime('%Y-%m-%d')
    


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
    WHERE FROM_UNIXTIME(m.match_time, '%Y-%m-%d') = '{}'
    ORDER BY `m`.`match_time` DESC
    LIMIT {} OFFSET {}               
    """.format(formatted_date_today,bulk,offset_number))


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
            print(match_dict[index]['match_id']) 
    return match_dict
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
        homeaway_h2h = json.loads(match_data['h2h'])[0]['matches']
        ##home and away head2head stats
        #team1 as home 
        team1_h2h_home_scores = []
        for i in homeaway_h2h:
            if i['home_name']== team1:
                team1_h2h_home_scores.append(i['home_scores'][0])
        #team2 as away
        team2_h2h_away_scores = []
        for i in homeaway_h2h:
            if i['away_name']== team2:
                team2_h2h_away_scores.append(i['away_scores'][0]) 
            
        
        #Avg team 1 h2h home scores 5 recent games
        team1_avg_h2h_home_scores = np.mean(team1_h2h_home_scores[0:5]) if len(team1_h2h_home_scores[0:5]) > 0 else 0
        #Avg team 2 h2h away score 5 recent games
        team2_avg_h2h_away_scores = np.mean(team2_h2h_away_scores[0:5]) if len(team2_h2h_away_scores[0:5]) > 0 else 0

        #H2H recents 5 games
        homeaway_h2h = json.loads(match_data['h2h'])[0]['matches'][0:5]
        team1_h2h_stats = {'win':0,'draw':0,'loss':0}
        for i in homeaway_h2h:
            if i['home_scores'] > i['away_scores']:
                if i['home_name'] == team1:
                    team1_h2h_stats['win']+=1
                else:
                    team1_h2h_stats['loss']+=1
            elif i['home_scores'] == i['away_scores']:
                team1_h2h_stats['draw']+=1
            else:
                if i['home_name'] == team1:
                    team1_h2h_stats['loss']+=1
                else:
                    team1_h2h_stats['win']+=1
        #Team1 stats 5 recent games:
        home_stats = {'win':0,'draw':0,'loss':0}
        homeaway_home  =  json.loads(match_data['home'])[0]['matches'][0:5]
        for i in homeaway_home:
            if i['home_scores'] > i['away_scores']:
                if i['home_name'] == team1:
                    home_stats['win']+=1
                else:
                    home_stats['loss']+=1
            elif i['home_scores'] == i['away_scores']:
                home_stats['draw']+=1
            else:
                if i['home_name'] == team1:
                    home_stats['loss']+=1
                else:
                    home_stats['win']+=1
        #Team2 stats 5 recent games
        away_stats = {'win':0,'draw':0,'loss':0}
        homeaway_away =  json.loads(match_data['away'])[0]['matches'][0:5]
        for i in homeaway_away:
            if i['home_scores'] > i['away_scores']:
                if i['home_name'] == team2:
                    away_stats['win']+=1
                else:
                    away_stats['loss']+=1
            elif i['home_scores'] == i['away_scores']:
                away_stats['draw']+=1
            else:
                if i['home_name'] == team2:
                    away_stats['loss']+=1
                else:
                    away_stats['win']+=1
        #Team1 GA and GF scores
        #team1_home_ga_scores=[]
        team1_home_gf_scores=[]
        homeaway_home = json.loads(match_data['home'])[0]['matches']
        for i in homeaway_home:
            if i['home_name']== team1:
                #team1_home_ga_scores.append(i['home_scores'][0])
                team1_home_gf_scores.append(i['away_scores'][0])
        team1_avg_home_gf_scores = np.mean(team1_home_gf_scores) if len(team1_home_gf_scores) > 0 else 0
        team2_away_gf_scores=[]
        homeaway_away = json.loads(match_data['away'])[0]['matches']
        for i in homeaway_away:
            if i['away_name']== team2:
                team2_away_gf_scores.append(i['away_scores'][0])
                #team2_away_gf_scores.append(i['home_scores'][0])
        team2_avg_away_gf_scores = np.mean(team2_away_gf_scores) if len(team2_away_gf_scores) > 0 else 0
    
        #team1_home_eg_adjst_ratio = (team1_avg_h2h_home_scores + team1_avg_home_gf_scores)/2
        #team2_away_eg_adjst_ratio = (team2_avg_h2h_away_scores + team2_avg_away_gf_scores)/2
        #Home and Away EG
        home_eg = (team1_avg_h2h_home_scores + team1_avg_home_gf_scores)/2
        away_eg = (team2_avg_h2h_away_scores + team2_avg_away_gf_scores)/2
        def poisson_goal(g,eg):
            return (math.e**(-eg)*eg**g)/(math.factorial(g))
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
        print('hahahah') 
match_dict = get_matches(190,conn,20)
for keys, values in match_dict.items():
        try:
            match_data = match_dict[keys]
            team1,team2,league_name,day_of_week_vi,date_dmy,time_hm,stadium,team1_h2h_stats,home_stats,away_stats,home_goal_pred,away_goal_pred,home_win_prob,away_win_prob,draw_prob,both_team_score_prob,home_goals_probs,away_goals_probs,match_id = get_match_info(match_data)
            #analysis = write_content4turbo(team1,team2,league_name,day_of_week_vi,date_dmy,time_hm,stadium,team1_h2h_stats,home_stats,away_stats,home_goal_pred,away_goal_pred,home_win_prob,away_win_prob,draw_prob,both_team_score_prob)
            #match_data['analysis'] = analysis
            print(match_id)
        except Exception as e:
            print(match_dict[keys])
