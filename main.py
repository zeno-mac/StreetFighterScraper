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
archiveEnabled = False
mode_code = {
    "ranked" : "/rank",
    "casual" : "/casual",
    "custom_room" : "/custom",
    "battle_hub" : "/hub",
    "all" : ""
}


def log(string):
    if logEnabled == True:
        print(string)
        
def errorLog(string):
    print(string)
    quit()

def translateInput(name):
    classic = "[t]クラシック"
    modern = "[t]モダン"
    if name == classic:
        return "classic"
    elif name == modern:
        return "modern"
    else:
        raise Exception(f"{name} not in found in input types")

def translateResult(results):
    table = {
    0 : "L",
    1 : "V",
    2 : "C",
    3 : "T(?)",
    4 : "D",
    5 : "OD",
    6 : "SA",
    7 : "CA",
    8 : "P"
    }
    res = []
    for i in results:
        r = table.get(i,"")
        res.append(r)
    return res

def checkWin(results):
    return "L" if (results.count(0) == 2) else "W"
        
def fillMatch(match, my_info, opp_info, side):
    my_round = translateResult(my_info["round_results"])
    opp_round = translateResult(my_info["round_results"])
    if len(my_round) == 2:
        my_round.append("")
        opp_round.append("")
    m ={
                "id": match["replay_id"],
                "res": checkWin(my_info["round_results"]),
                "uploaded_at" :match["uploaded_at"],"side": side,
                "id": match["replay_id"],
                "res": checkWin(my_info["round_results"]),
                "uploaded_at" :match["uploaded_at"],
                "date": datetime.fromtimestamp(match["uploaded_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "mode": match["replay_battle_type_name"],
                "my_character":my_info["character_name"],
                "my_MR":my_info["master_rating"],
                "my_input_type":translateInput(my_info["battle_input_type_name"]),
                "my_LP":my_info["league_point"],
                "my_ranking":my_info["master_rating_ranking"],
                "my_round1":my_round[0],
                "my_round2":my_round[1],
                "my_round3":my_round[2],
                "opp_name": opp_info["player"]["fighter_id"],
                "opp_id": opp_info["player"]["short_id"],
                "opp_platflorm": opp_info["player"]["platform_name"],
                "opp_round1":opp_round[0],
                "opp_round2":opp_round[1],
                "opp_round3":opp_round[2],
                "opp_character":opp_info["character_name"],
                "opp_MR":opp_info["master_rating"],
                "opp_input_type":translateInput(opp_info["battle_input_type_name"]),
                "opp_LP":opp_info["league_point"],
                "opp_ranking":opp_info["master_rating_ranking"],
                "date": datetime.fromtimestamp(match["uploaded_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "side": side,
                "my_character":my_info["character_name"],
                "my_MR":my_info["master_rating"],
                "my_input_type":translateInput(my_info["battle_input_type_name"]),
                "my_LP":my_info["league_point"],
                "my_ranking":my_info["master_rating_ranking"],
                "my_round1":my_round[0],
                "my_round2":my_round[1],
                "my_round3":my_round[2],
                "opp_name": opp_info["player"]["fighter_id"],
                "opp_id": opp_info["player"]["short_id"],
                "opp_platflorm": opp_info["player"]["platform_name"],
                "opp_round1":opp_round[0],
                "opp_round2":opp_round[1],
                "opp_round3":opp_round[2],
                "opp_character":opp_info["character_name"],
                "opp_MR":opp_info["master_rating"],
                "opp_input_type":translateInput(opp_info["battle_input_type_name"]),
                "opp_LP":opp_info["league_point"],
                "opp_ranking":opp_info["master_rating_ranking"],
    }
    return m

def parseMatch(match):
    if "replay_id" not in match or "uploaded_at" not in match:
            errorLog(f"Missing replay_id or uploaded_at in match: {match.get('replay_id')}")
    try:
        side = ""
        player1_id = str(match["player1_info"]["player"]["short_id"])
        player2_id = str(match["player2_info"]["player"]["short_id"])
        if (player1_id==USER_ID):
            side = "Right side"
            my_info  = match["player1_info"]
            opp_info = match["player2_info"]
        elif (player2_id==USER_ID):
            side = "Left Side"
            my_info = match["player2_info"]
            opp_info = match["player1_info"]
        else:
            raise KeyError(f"User_id ({USER_ID} not found, player1_id = {player1_id}, player2_id = {player2_id}")
        
        required = ["character_name", "master_rating", "battle_input_type_name","league_point","master_rating_ranking"]
        missing = [k for k in required if k not in my_info]
        if missing:
            raise KeyError(f"Missing keys in player info: {missing}")
        cleanedMatch = fillMatch(match, my_info, opp_info, side)
    except  Exception as e:
        errorLog(f"Error occurred during battlelog cleaning: {e}")
    return cleanedMatch
    
def archive(battlelog):
    if not archiveEnabled:
        return
    path = 'log.json'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    existing_keys = {item.get('uploaded_at') for item in existing if 'uploaded_at' in item}
    new_items = [item for item in battlelog if item.get('uploaded_at') not in existing_keys]
    if not new_items:
        return

    existing.extend(new_items)
    existing.sort(key=lambda x: x.get('uploaded_at', 0))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def scrapeMode(mode):
    battlelog = []
    for i in range(10):
        url = "https://www.streetfighter.com/6/buckler/it/profile/"+USER_ID+"/battlelog"+mode_code[mode]+"?page="+str(i+1)
        log(f"Sending http request n{i+1} to {url}...")
        contents = requests.get(url,headers=headers,cookies=cookies)
        if(contents.status_code == 200):
            log(f'Successful: status code {contents.status_code}')
        else:
            errorLog(f'Error during request n{i+1}: status code {contents.status_code}')
        log("Parsing html content...")
        try:
            soup = BeautifulSoup(contents.content, "html.parser")
            next_data = soup.find("script" , id = "__NEXT_DATA__")
            parsed = json.loads(next_data.string)
            partialBattlelog = parsed["props"]["pageProps"]["replay_list"]
        except Exception as e:
            errorLog(f"Error occurred during html parsing: {e}")
        battlelog.extend(partialBattlelog)
        if len(partialBattlelog) != 10:
            log("Found the end of content, stopped the scraping process early")
            break
    return battlelog
    
matches = []
battlelog = scrapeMode("ranked")

archive(battlelog)
    
for match in battlelog:
    cleanedMatch = parseMatch(match)
    matches.append(cleanedMatch)


matches = sorted(matches, key=lambda x: x["uploaded_at"])
#open("cleanedlog3.json", "w", encoding="utf-8").write(json.dumps(matches, ensure_ascii=False, indent=2))



log("Starting http request to Google App Scripts")
r = requests.post(APP_SCRIPT_URL, json=matches)
if r.status_code == 200:
    log(f"Successful: status code {r.text}")
else:
    errorLog(f"Error occurred during Google App Scripts request: status code {r.status_code}\nError: {r.text}")
    

    
