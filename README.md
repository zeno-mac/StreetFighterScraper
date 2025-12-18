# Basic webscraper of battlelog from streetfighter.com

## Usage

Run the script via Python 'python main.py', with no arguments the program will scrape the last 100 matches of any mode. By adding arguments (ranked , casual, custom, hub) it will scrape only the last 100 matches of that specific modes, it's also possible to to scape multipe modes at once.
E.g. 'python main.py ranked hub' will scrape both the last 100 ranked matches and the last 100 battle hub matches.

## Setup

The script will be easy to use, but it first requires some setup to get everything running.

### Directory Setup

Rename .env.example to .env, this file will contain all your personal data, don't share it with anyone!

### Google App Scripts Setup

First, we need to create a Google Sheets project, and add a script to it that will let us add data from the python script.
If you want to have some simple tables and graphs already set up you can make a copy [my sheet](https://docs.google.com/spreadsheets/d/1DMioCa5-V0UWB21HtBkEVNNTrZg84Wu4DwcJ3m6xP5Y/edit?usp=sharing). If you don't just create a blank spreadsheet and rename the base sheet to "Data".

Go to Extension > App Script.

Replace the content of Code.gs with the content from Parser.gs

Deploy the code by going to Deploy > New Deployment.

Select the type "Web App" and set access to "Anyone".

You need to authorise the developer (you) to access your data.

From here copy the Web App URL into the APP_SCRIPT_URL field in env file.

If you lose the url you can retrieve it again by going in Deploy > Manage Deployment

### Scraper setup

Now we'll handle the scraper part, Capcom locks the contents unless you log in, so we need to retrieve the id that'll let the script to log in. 

We also need to get our User Code, so that the script knows where to actually look for.

Go to [Buckler's Boot Camp](https://www.streetfighter.com/6/buckler) and head into your profile page.

In your banner copy the User Code and paste it in the USER_CODE field in the env file.

Getting the id for login is a bit more tricky and the exact steps depends on the browser. The goal is to inspect the cookies, and copy the "buckler_id" value.

On Firefox you can go into Storage tab by pressing Shift+F9 (or F12 > Storage) > Cookies.

On Chrome press F12 > Application tab > Cookies

Once you are in the Cookies select streetfighter.com section, you'll a few different values, look for "buckler_id" (ignore "buckler_r_id", we
don't care about that), the value should be a long alphanumeric code.

Once you find it copy the value and paste in the "BUCKLER_ID" field. This id might expiry, if the script stops working check if there's a new one!

### Python setup

To run the script you need to install [Python](https://www.python.org/downloads/), create a virtual environment (where you'll downloand all the libraries necessary) and then download the library. (I'm not an expert on different python environment, the commands might be a little different based on your OS)

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

## Configuration

The configuration you find in config.json offers some tweak for your experience.

-is_debug_archive_enabled: before the script parse the matches it stores them in debug_log.json with all the data that Capcom stores;

-is_archive_enabled: before the script send the message to Google Sheet it stores them in log.json with only the interesting data;

-max_requests: how many requests the script sends it simultaneously the the Capcom server, more than 10 is useless since the script only scrape one mode at a time;

-debug: print all the information about the flow of the script in the terminal;

-page_to_scrape: how many pages the script scrapes, each mode has 10 pages with 10 match each. If you want to be sure you can scrape all of the matches since it won't create any duplicate on Sheet
