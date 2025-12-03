import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os

load_dotenv()

USER_AGENT = os.getenv("USER_AGENT")
BUCKLER_ID = os.getenv("BUCKLER_ID")
USER_ID = os.getenv("USER_ID")
cookies = {'buckler_id' : BUCKLER_ID}
headers = {'User-Agent': USER_AGENT}




contents = requests.get("https://www.streetfighter.com/6/buckler/it/profile/"+USER_ID+"/battlelog/rank#profile_na",headers=headers,cookies=cookies)
print(contents.status_code)
if(contents.status_code == 200):
    soup = BeautifulSoup(contents.content, "html.parser")
    logClass = "battle_data_battlelog__list__JNDjG"
    data = soup.find("script" , id = "__NEXT_DATA__")
    parsed = json.loads(data.string)
    open("next_data.json", "w", encoding="utf-8").write(json.dumps(parsed, ensure_ascii=False, indent=2))
    battlelog = parsed["props"]["pageProps"]["replay_list"]
    open("log.json", "w", encoding="utf-8").write(json.dumps(battlelog, ensure_ascii=False, indent=2))
    open("index.html", "w").write(str(soup.body.prettify()))
    parsedMatches = []
    for match in battlelog:
        if (match["player1_info"]["player"]["short_id"]== USER_ID):
            parsedMatch={
                "id": match["replay_id"],
                "me":{
                    "character": match["player1_info"]["character_name"],
                }
                ,
                "opponent":{
                    "character":match["player2_info"]["character_name"],
                }

            }
        else:
            parsedMatch={
                "id": match["replay_id"],
                "me":{
                    "character": match["player2_info"]["character_name"],
                }
                ,
                "opponent":{
                    "character":match["player1_info"]["character_name"],
                }

            }
        parsedMatches.append(parsedMatch)
    
    open("cleanedlog.json", "w", encoding="utf-8").write(json.dumps(parsedMatches, ensure_ascii=False, indent=2))
    
    
    

    
