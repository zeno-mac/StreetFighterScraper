import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor
import itertools
import logging
from dataclasses import dataclass



@dataclass(frozen=True)
class Config:
    user_id: str
    app_script_url: str
    headers: dict
    cookies: dict
    mode_code: dict[str, str]
    max_workers: int = 10
    debug: bool = False
    is_archive_enabled: bool = False
    

logger = logging.getLogger(__name__)



def translateInput(name):
    if name == 1:
        return "Classic"
    elif name == 0:
        return "Modern"
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
    opp_round = translateResult(opp_info["round_results"])
    if len(my_round) == 2:
        my_round.append("")
        opp_round.append("")
    m ={
        "id": match["replay_id"],
        "side": side,
        "uploaded_at" :match["uploaded_at"],
        "date": datetime.fromtimestamp(match["uploaded_at"]).strftime("%Y-%m-%d %H:%M:%S"),
        "mode": match["replay_battle_type_name"],
        "res": checkWin(my_info["round_results"]),
        "my_character":my_info["character_name"],
        "my_MR":my_info["master_rating"],
        "my_input_type":translateInput(my_info["battle_input_type"]),
        "my_LP":my_info["league_point"],
        "my_ranking":my_info["master_rating_ranking"],
        "my_round1":my_round[0],
        "my_round2":my_round[1],
        "my_round3":my_round[2],
        "opp_name": opp_info["player"]["fighter_id"],
        "opp_id": opp_info["player"]["short_id"],
        "opp_platform": opp_info["player"]["platform_name"],
        "opp_round1":opp_round[0],
        "opp_round2":opp_round[1],
        "opp_round3":opp_round[2],
        "opp_character":opp_info["character_name"],
        "opp_MR":opp_info["master_rating"],
        "opp_input_type":translateInput(opp_info["battle_input_type"]),
        "opp_LP":opp_info["league_point"],
        "opp_ranking":opp_info["master_rating_ranking"],
                }
    return m

def parseMatch(cfg : Config, match):
    if "replay_id" not in match or "uploaded_at" not in match:
            raise KeyError(f"Missing replay_id or uploaded_at in match: {match.get('replay_id')}")
    try:
        side = ""
        player1_id = str(match["player1_info"]["player"]["short_id"])
        player2_id = str(match["player2_info"]["player"]["short_id"])
        if (player1_id==cfg.user_id):
            side = "Left side"
            my_info  = match["player1_info"]
            opp_info = match["player2_info"]
        elif (player2_id==cfg.user_id):
            side = "Right side"
            my_info = match["player2_info"]
            opp_info = match["player1_info"]
        else:
            raise KeyError(f"User_id ({cfg.user_id} not found, player1_id = {player1_id}, player2_id = {player2_id}")
        
        required = ["character_name", "master_rating", "battle_input_type_name","league_point","master_rating_ranking"]
        missing = [k for k in required if k not in my_info]
        if missing:
            raise KeyError(f"Missing keys in player info: {missing}")
        cleanedMatch = fillMatch(match, my_info, opp_info, side)
    except  Exception as e:
        raise KeyError(f"Error occurred during battlelog cleaning: {e}")
    return cleanedMatch
    
def archive(cfg: Config, battlelog):
    if not cfg.is_archive_enabled:
        return
    path = 'log.json'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    existing_keys = {item.get('replay_id') for item in existing if 'replay_id' in item}
    new_items = [item for item in battlelog if item.get('replay_id') not in existing_keys]
    if not new_items:
        return

    existing.extend(new_items)
    existing.sort(key=lambda x: x.get('uploaded_at', 0))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def send_sf_request(cfg: Config, mode, index):
    url = "https://www.streetfighter.com/6/buckler/it/profile/"+cfg.user_id+"/battlelog"+cfg.mode_code[mode]+"?page="+str(index)
    contents = requests.get(url,headers=cfg.headers,cookies=cfg.cookies)
    if(contents.status_code != 200):
        raise KeyError(f'Error during request to {url} status code {contents.status_code}')
    soup = BeautifulSoup(contents.content, "html.parser")
    next_data = soup.find("script" , id = "__NEXT_DATA__")
    parsed = json.loads(next_data.string)
    partialBattlelog = parsed["props"]["pageProps"]["replay_list"]
    return partialBattlelog
     
def send_gas_request(cfg: Config, data):
    logger.debug("Starting http request to Google App Scripts")
    r = requests.post(cfg.app_script_url, json=data)
    if r.status_code == 200:
        if "GAS" in r.text:
            raise KeyError(f"Script returned an error: {r.text}")
        else:
            logger.debug(f"Successful: {r.text}")
    else:
        raise KeyError(f"Error occurred during Google App Scripts request: status code {r.status_code}\nError: {r.text}")
      
def scrapeMode(cfg: Config, mode):
    battlelog = []
    with ThreadPoolExecutor(max_workers=cfg.max_workers) as ex:
        results = list(ex.map(send_sf_request,itertools.repeat(cfg),itertools.repeat(mode), range(1, 11)))
    for bt in results:
        battlelog.extend(bt)
    return battlelog

def scrapeLog(cfg: Config,battlelog):    
    matches = []
    for match in battlelog:
        cleanedMatch = parseMatch(cfg,match)
        matches.append(cleanedMatch)
    return matches

def setup_config():
    MODE_CODE = {
    "ranked" : "/rank",
    "casual" : "/casual",
    "custom" : "/custom",
    "hub" : "/hub",
    "all" : ""
}
    load_dotenv()
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    cfg = Config(
        user_id=os.getenv("USER_ID"),
        app_script_url=os.getenv("APP_SCRIPT_URL"),
        headers={"User-Agent": os.getenv("USER_AGENT")},
        cookies={"buckler_id": os.getenv("BUCKLER_ID")},
        mode_code=MODE_CODE,
        max_workers= config.get("max_requests", 10),
        debug= config.get("debug", False)
    )
    return cfg

def setup_logger(cfg:Config):
    if cfg.debug:
        logging.basicConfig(
        level=getattr(logging, "DEBUG", logging.INFO),
        format="%(levelname)s %(asctime)s : %(message)s"
        )
    else:
        logging.basicConfig(
        level=getattr(logging, "INFO", logging.INFO),
        format="%(levelname)s : %(message)s"
        )              

def main():
    cfg = setup_config()
    setup_logger(cfg)
    
    modes = []
    args = sys.argv[1:]

    if not args:
        modes = ["all"]
    for arg in args:
        if arg in cfg.mode_code:
            modes.append(arg)
        else:
            raise KeyError(f"Error: {arg} not found in the modes")

    logger.info(f"Starting the scraping of the modes:{modes}")    

    battlelog = []
    for mode in modes:
        bt = scrapeMode(cfg,mode)
        battlelog.extend(bt)

    logger.info(f"Successful scraping")    
    archive(cfg,battlelog)

    logger.info("Starting the parsing process...")
    parsed_log= scrapeLog(cfg, battlelog)
    logger.info("Successful parsing")

    send_gas_request(cfg,parsed_log)
 
if __name__ == "__main__":
    main()