import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
from datetime import datetime


load_dotenv()

USER_AGENT = os.getenv("USER_AGENT")
BUCKLER_ID = os.getenv("BUCKLER_ID")
USER_ID = os.getenv("USER_ID")
APP_SCRIPT_URL = os.getenv("APP_SCRIPT_URL")
cookies = {'buckler_id' : BUCKLER_ID}
headers = {'User-Agent': USER_AGENT}
logEnabled = True
def log(string):
    if logEnabled == True:
        print(string)
        
def errorLog(string):
    print(string)
    quit()
    
def fillPlayerInfo(player):
    required = ["character_name", "master_rating", "battle_input_type_name"]
    missing = [k for k in required if k not in player]
    if missing:
        raise KeyError(f"Missing keys in player info: {missing}")
    info = {
        "character":player["character_name"],
        "MR":player["master_rating"],
        "input_type":translateInput(player["battle_input_type_name"]),
        } 
 
    return info
    

def translateInput(name):
    classic = "[t]クラシック"
    modern = "[t]モダン"
    if name == classic:
        return "classic"
    elif name == modern:
        return "modern"
    else:
        raise Exception(f"{name} not in found in input types")
    
matches = []
for i in range(10):
    log(f"Sending http request n°{i+1} to Capcom...")
    contents = requests.get("https://www.streetfighter.com/6/buckler/it/profile/"+USER_ID+"/battlelog/rank?page="+str(i+1),headers=headers,cookies=cookies)
    if(contents.status_code != 200):
        errorLog(f'Error during request n°{i+1}: status code {contents.status_code}')
        
    else:
        log(f'Successful: status code {contents.status_code}')
    log("Parsing html content...")
    try:
        soup = BeautifulSoup(contents.content, "html.parser")
        next_data = soup.find("script" , id = "__NEXT_DATA__")
        parsed = json.loads(next_data.string)
        battlelog = parsed["props"]["pageProps"]["replay_list"]
    except Exception as e:
        errorLog(f"Error occurred during html parsing: {e}")
        
    #open("next_data.json", "w", encoding="utf-8").write(json.dumps(parsed, ensure_ascii=False, indent=2)) 
    #open("log.json", "w", encoding="utf-8").write(json.dumps(battlelog, ensure_ascii=False, indent=2))
    ##open("index.html", "w", encoding="utf-8").write(str(soup.body.prettify()))
    
    
    for match in battlelog:
        if "replay_id" not in match or "uploaded_at" not in match:
                errorLog(f"Missing replay_id or uploaded_at in match: {match.get('replay_id')}")
        try:
            player1_id = str(match["player1_info"]["player"]["short_id"])
            player2_id = str(match["player2_info"]["player"]["short_id"])
            if (player1_id==USER_ID):
                my_info  = match["player1_info"]
                opponent_info = match["player2_info"]
            elif (player2_id==USER_ID):
                my_info = match["player2_info"]
                opponent_info = match["player1_info"]
            else:
                raise KeyError(f"User_id ({USER_ID} not found, player1_id = {player1_id}, player2_id = {player2_id}")
            
            required = ["character_name", "master_rating", "battle_input_type_name"]
            missing = [k for k in required if k not in my_info]
            if missing:
                raise KeyError(f"Missing keys in player info: {missing}")
            parsedMatch={
                "id": match["replay_id"],
                "uploaded_at" :match["uploaded_at"],
                "date": datetime.fromtimestamp(match["uploaded_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "my_character":my_info["character_name"],
                "my_MR":my_info["master_rating"],
                "my_input_type":translateInput(my_info["battle_input_type_name"]),
                "opp_character":opponent_info["character_name"],
                "opp_MR":opponent_info["master_rating"],
                "opp_input_type":translateInput(opponent_info["battle_input_type_name"]),
            }
        except  Exception as e:
            errorLog(f"Error occurred during battlelog cleaning: {e}")
        matches.append(parsedMatch)
            
            
matches.reverse()
##open("cleanedlog.json", "w", encoding="utf-8").write(json.dumps(matches, ensure_ascii=False, indent=2))
r = requests.post(APP_SCRIPT_URL, json=matches)
log("Starting http request to Google App Scripts")
if r.status_code == 200:
    log(f"Successful: status code {r.status_code}")
else:
    errorLog(f"Error occurred during Google App Scripts request: status code {r.status_code}\nError: {r.text}")
    

    
