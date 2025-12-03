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
cookies = {'buckler_id' : BUCKLER_ID}
headers = {'User-Agent': USER_AGENT}


def fillPlayerInfo(player):
    info = {
        "character":player["character_name"],
        "MR":player["master_rating"],
        "input_type":transleInput(player["battle_input_type_name"]),
        }
    return info

def transleInput(name):
    classic = "[t]クラシック"
    modern = "[t]モダン"
    if name == classic:
        return "classic"
    else:
        return "modern"
    
parsedMatches = []
for i in range(10):
    contents = requests.get("https://www.streetfighter.com/6/buckler/it/profile/"+USER_ID+"/battlelog/rank?page="+str(i+1),headers=headers,cookies=cookies)
    print(contents.status_code)
    if(contents.status_code == 200):
        soup = BeautifulSoup(contents.content, "html.parser")
        logClass = "battle_data_battlelog__list__JNDjG"
        next_data = soup.find("script" , id = "__NEXT_DATA__")
        parsed = json.loads(next_data.string)
        battlelog = parsed["props"]["pageProps"]["replay_list"]
 
        #open("next_data.json", "w", encoding="utf-8").write(json.dumps(parsed, ensure_ascii=False, indent=2)) 
        #open("log.json", "w", encoding="utf-8").write(json.dumps(battlelog, ensure_ascii=False, indent=2))
        ##open("index.html", "w", encoding="utf-8").write(str(soup.body.prettify()))
        
        for match in battlelog:
            if (str(match["player1_info"]["player"]["short_id"])== USER_ID):
                my_info  = match["player1_info"]
                opponent_info = match["player2_info"]
            else:
                my_info = match["player2_info"]
                opponent_info = match["player1_info"]
            
            parsedMatch={
                "id": match["replay_id"],
                "uploaded_at" :match["uploaded_at"],
                "date": datetime.fromtimestamp(match["uploaded_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "me": fillPlayerInfo(my_info),
                "opponent":fillPlayerInfo(opponent_info),
            }
            parsedMatches.append(parsedMatch)
parsedMatches.reverse()
open("cleanedlog.json", "w", encoding="utf-8").write(json.dumps(parsedMatches, ensure_ascii=False, indent=2))
    
    
    

    
