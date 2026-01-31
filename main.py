import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor
import itertools
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Config:
    user_code: str
    app_script_url: str
    headers: dict
    cookies: dict
    max_workers: int = 10
    debug: bool = False
    is_debug_archive_enabled: bool = False
    is_archive_enabled: bool = False
    page_to_scrape: int = 10

class Scraper:
    cfg: Config
    
    mode_code = {
    "ranked" : "/rank",
    "casual" : "/casual",
    "custom" : "/custom",
    "hub" : "/hub",
    "all" : ""
    }
    class AuthenticationError(Exception):
        """Raised when authentication fails (403 status code)"""
        pass

    def __init__(self,cfg_input:Config):
        self.cfg=cfg_input
        
    def send_sf_request(self,mode, index):
        url = "https://www.streetfighter.com/6/buckler/it/profile/"+self.cfg.user_code+"/battlelog"+self.mode_code[mode]+"?page="+str(index)
        contents = requests.get(url,headers=self.cfg.headers,cookies=self.cfg.cookies)
        if(contents.status_code == 403):
            raise self.AuthenticationError(f'Error during request to {url} status code {contents.status_code}, forbidden access, try checking your User Agent or your Buckler ID')
        elif(contents.status_code == 400):
            raise KeyError(f'Error during request to {url} status code {contents.status_code}, bad request, try checking your User Code')
        elif(contents.status_code != 200):
            raise KeyError(f'Error during request to {url} status code {contents.status_code}')
        soup = BeautifulSoup(contents.content, "html.parser")
        next_data = soup.find("script" , id = "__NEXT_DATA__")
        parsed = json.loads(next_data.string)
        partialBattlelog = parsed["props"]["pageProps"].get("replay_list",None)
        if partialBattlelog is None:
            raise KeyError(f"Error during request to {url}, no history found, try checking you User Code")
        return partialBattlelog
    
    def updateID(self):
        new_buckler_id = input("It seems the Buckler ID is no longer valid, please provide the new one:").strip()
    
        env_lines = []
        buckler_updated = False

        with open(".env", "r", encoding="utf-8") as f:
            env_lines = f.readlines()
        for i, line in enumerate(env_lines):
            if line.strip().startswith("BUCKLER_ID="):
                env_lines[i] = f"BUCKLER_ID={new_buckler_id}\n"
                buckler_updated = True
                break
            
        if not buckler_updated:
            env_lines.append(f"BUCKLER_ID={new_buckler_id}\n")
        try:
            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(env_lines)
            self.cfg.cookies["buckler_id"] = new_buckler_id
            print("[+] Buckler ID updated successfully!")
        except Exception as e:
            print(f"Error writing to .env file: {e}")
        
    def scrapeModes(self,modes):
        log = []
        while(True):
            try:
                self.send_sf_request("all", 0)
                break
            except self.AuthenticationError as e:
                self.updateID()
        for mode in modes:
            if mode not in self.mode_code:
                logger.warning(f"Mode: {mode} not found in mode list")
            else:
                bt = self.scrapeMode(mode)
                log.extend(bt)
        return log
    
    def scrapeMode(self,mode):
        battlelog = []
        with ThreadPoolExecutor(max_workers=self.cfg.max_workers) as ex:
            results = list(ex.map(self.send_sf_request,itertools.repeat(mode), range(1, self.cfg.page_to_scrape +1)))
        for bt in results:
            battlelog.extend(bt)
        return battlelog
    
class Parser:
    
    cfg: Config
    
    def __init__(self,cfg_input:Config):
        self.cfg=cfg_input
        
    def translate_input(self,name):
        if name == 0:
            return "Classic"
        elif name == 1:
            return "Modern"
        else:
            raise Exception(f"{name} not in found in input types")

    def get_rank(self, LP, MR):
        ranks = [
        {"threshold": 25000, "label": "Master"},
        {"threshold": 23800, "label": "Diamond 5"},
        {"threshold": 22600, "label": "Diamond 4"},
        {"threshold": 21400, "label": "Diamond 3"},
        {"threshold": 20200, "label": "Diamond 2"},
        {"threshold": 19000, "label": "Diamond 1"},
        {"threshold": 17800, "label": "Platinum 5"},
        {"threshold": 16600, "label": "Platinum 4"},
        {"threshold": 15400, "label": "Platinum 3"},
        {"threshold": 14200, "label": "Platinum 2"},
        {"threshold": 13000, "label": "Platinum 1"},
        {"threshold": 12200, "label": "Gold 5"},
        {"threshold": 11400, "label": "Gold 4"},
        {"threshold": 10600, "label": "Gold 3"},
        {"threshold": 9800,  "label": "Gold 2"},
        {"threshold": 9000,  "label": "Gold 1"},
        {"threshold": 8200,  "label": "Silver 5"},
        {"threshold": 7400,  "label": "Silver 4"},
        {"threshold": 6600,  "label": "Silver 3"},
        {"threshold": 5800,  "label": "Silver 2"},
        {"threshold": 5000,  "label": "Silver 1"},
        {"threshold": 4600,  "label": "Bronze 5"},
        {"threshold": 4200,  "label": "Bronze 4"},
        {"threshold": 3800,  "label": "Bronze 3"},
        {"threshold": 3400,  "label": "Bronze 2"},
        {"threshold": 3000,  "label": "Bronze 1"},
        {"threshold": 2600,  "label": "Iron 5"},
        {"threshold": 2200,  "label": "Iron 4"},
        {"threshold": 1800,  "label": "Iron 3"},
        {"threshold": 1400,  "label": "Iron 2"},
        {"threshold": 1000,  "label": "Iron 1"},
        {"threshold": 800,   "label": "Rookie 5"},
        {"threshold": 600,   "label": "Rookie 4"},
        {"threshold": 400,   "label": "Rookie 3"},
        {"threshold": 200,   "label": "Rookie 2"},
        {"threshold": 0,     "label": "Rookie 1"},]

        if MR > 0:
            if MR > 1800:
                return "Ultimate Master"
            elif MR > 1700:
                return "Grand Master"
            elif MR > 1600:
                return "High Master"
            else:
                return "Master"
            
        rank_obj = next((r for r in ranks if LP >= r["threshold"]), None)
        return rank_obj["label"] if rank_obj else None
    
    def translate_result(self, results):
        table = {
        0 : "L",
        1 : "V",
        2 : "C",
        3 : "T",
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

    def checkWin(self, results):
        return "L" if (results.count(0) == 2) else "W"

    def fillMatch(self,match, my_info, opp_info, side):
        my_round = self.translate_result(my_info["round_results"])
        opp_round = self.translate_result(opp_info["round_results"])
        if len(my_round) == 2:
            my_round.append("")
            opp_round.append("")
        m ={
            "Id": match["replay_id"],
            "Side": side,
            "Uploaded at" :match["uploaded_at"],
            "Date": datetime.fromtimestamp(match["uploaded_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            "Mode": match["replay_battle_type_name"],
            "Result": self.checkWin(my_info["round_results"]),
            "My Character":my_info["character_name"],
            "My MR":my_info["master_rating"],
            "My Input Type":self.translate_input(my_info["battle_input_type"]),
            "My LP":my_info["league_point"],
            "My Ranking":my_info["master_rating_ranking"],
            "My Rank": self.get_rank(my_info["league_point"],my_info["master_rating"]),
            "My Round 1":my_round[0],
            "My Round 2":my_round[1],
            "My Round 3":my_round[2],
            "Opp Name": opp_info["player"]["fighter_id"],
            "Opp Id": opp_info["player"]["short_id"],
            "Opp Platform": opp_info["player"]["platform_name"],
            "Opp Round1":opp_round[0],
            "Opp Round2":opp_round[1],
            "Opp Round3":opp_round[2],
            "Opp Character":opp_info["character_name"],
            "Opp MR":opp_info["master_rating"],
            "Opp Input Type":self.translate_input(opp_info["battle_input_type"]),
            "Opp LP":opp_info["league_point"],
            "Opp Rank": self.get_rank(opp_info["league_point"],opp_info["master_rating"]),
            "Opp Ranking":opp_info["master_rating_ranking"],
                    }
        return m

    def parseMatch(self, match):
        if "replay_id" not in match or "uploaded_at" not in match:
                raise KeyError(f"Missing replay_id or uploaded_at in match: {match.get('replay_id')}")
        try:
            side = ""
            player1_id = str(match["player1_info"]["player"]["short_id"])
            player2_id = str(match["player2_info"]["player"]["short_id"])
            if (player1_id==self.cfg.user_code):
                side = "Left side"
                my_info  = match["player1_info"]
                opp_info = match["player2_info"]
            elif (player2_id==self.cfg.user_code):
                side = "Right side"
                my_info = match["player2_info"]
                opp_info = match["player1_info"]
            else:
                raise KeyError(f"User code ({self.cfg.user_code} not found, player1_id = {player1_id}, player2_id = {player2_id}")

            required = ["character_name", "master_rating", "battle_input_type_name","league_point","master_rating_ranking"]
            missing = [k for k in required if k not in my_info]
            if missing:
                raise KeyError(f"Missing keys in player info: {missing}")
            cleanedMatch = self.fillMatch(match, my_info, opp_info, side)
        except  Exception as e:
            raise KeyError(f"Error occurred during battlelog cleaning: {e}")
        return cleanedMatch
    
    def parse_log(self,battlelog):    
        matches = []
        for match in battlelog:
            cleanedMatch = self.parseMatch(match)
            matches.append(cleanedMatch)
        return matches

def archive(path, battlelog, key):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []
    existing_keys = {item.get(key) for item in existing if key in item}
    new_items = [item for item in battlelog if item.get(key) not in existing_keys]
    logger.debug(f"Number of item in {path}: {len(existing)}")
    if not new_items:
        return
    existing.extend(new_items)
    existing.sort(key=lambda x: x.get('uploaded_at', 0))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def send_gas_request(cfg: Config, data):
    logger.debug("Starting http request to Google App Scripts")
    r = requests.post(cfg.app_script_url, json=data)
    if r.status_code == 200:
        if "GAS" in r.text:
            raise KeyError(f"Script returned an error: {r.text}")
        else:
            return r.text
    else:
        raise KeyError(f"Error occurred during Google App Scripts request: status code {r.status_code}\nError: {r.text}")

def create_interactive_env():
    print("\n" + "="*40)
    print("      FIRST TIME SETUP DETECTED")
    print("="*40)
    print("I need a few details to get started.\n")

    user_code = input("1. Enter your SF6 User Code (Short ID): ").strip()
    
    print("\n2. Go to streetfighter.com/6/buckler, login, press F12 -> Application -> Cookies.")
    buckler_id = input("   Paste your 'buckler_id' value here: ").strip()
    
    print("\n3. Enter your Google Web App URL.")
    app_url = input("   URL: ").strip()

    default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"USER_CODE={user_code}\n")
        f.write(f"BUCKLER_ID={buckler_id}\n")
        f.write(f"APP_SCRIPT_URL={app_url}\n")
        f.write(f"USER_AGENT={default_ua}\n")
    
    print("\n[+] .env file created successfully!")

def create_default_config():
    if not os.path.exists("config.json"):
        default_conf = {
            "max_requests": 10,
            "debug": False,
            "is_debug_archive_enabled": False,
            "is_archive_enabled": False,
            "page_to_scrape": 10
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(default_conf, f, indent=4)
        print("[+] Default config.json created!")

def check_env_requirement():
    requirements = ["USER_CODE", "APP_SCRIPT_URL", "USER_AGENT","BUCKLER_ID"]
    missing = False
    text = ""
    for r in requirements:
        env_r = os.getenv(r)
        if not env_r:
            env_r = input(f"It appears {r} is missing, please enter it again:  ").strip()
            missing = True
            text += f"{r}={env_r}\n"
    if missing:
        with open(".env", "a", encoding="utf-8") as f:
            f.write(text)
        load_dotenv(override=True)
            
def setup_config():
    
    if not os.path.exists(".env"):
        create_interactive_env()
    
    if not os.path.exists("config.json"):
        create_default_config()
        
    load_dotenv()
    
    check_env_requirement()
    
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    cfg = Config(
        user_code=os.getenv("USER_CODE"),
        app_script_url=os.getenv("APP_SCRIPT_URL"),
        headers={"User-Agent": os.getenv("USER_AGENT")},
        cookies={"buckler_id": os.getenv("BUCKLER_ID")},
        max_workers= config.get("max_requests", 10),
        debug= config.get("debug", False),
        is_debug_archive_enabled= config.get("is_debug_archive_enabled", False),
        is_archive_enabled= config.get("is_archive_enabled", False),
        page_to_scrape= config.get("page_to_scrape", 10),
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
    
    args = sys.argv[1:]
    cont = True
    while(cont):
        try:
            if not args:
                args = ["all"]
            logger.info(f"Starting the scraping of the modes: {args}") 
            scraper = Scraper(cfg)
            battlelog = scraper.scrapeModes(args)
            logger.info(f"Successful scraping")   
            if cfg.is_debug_archive_enabled:
                logger.info("Archived the full log")
                archive("debug_log.json",battlelog,"replay_id")

            parser = Parser(cfg)
            logger.info("Starting the parsing process...")
            parsed_log= parser.parse_log(battlelog)
            logger.info("Successful parsing")

            if cfg.is_archive_enabled:
                archive("log.json",parsed_log, "Id")
                logger.info("Archived the parsed log")

            logger.info("Sending data to Google Sheets...")
            res = send_gas_request(cfg,parsed_log)
            logger.info(f"Successful Google App Script request: {res}")
            sys.stdout.flush()
            i = input("Do you want to scrape again? [y]/n").strip()
            if i == "n" or i == "no":
                cont = False 
        except Exception as e:
            print(e)
 
if __name__ == "__main__":
    main()