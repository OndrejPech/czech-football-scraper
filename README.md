# Czech Football Scraper

## About the project

For personal use, I need simple data about games in the football league of my hometown. I made a Python project, which can scrape data from https://fotbalunas.cz and create JSON files with data about each game in the league. It contains dates, results, lineups, subs, goals, and cards.

The structure of the JSON file is a work in progress. Some data isn't used yet, but I keep them for future use. I have no experience with data analysis or data mining, so at this point I keep everything and will decide about details later.


## How to use it for your league?

On https://fotbalunas.cz, find your league and click on it.
The ID of the league is the last path of the URL. For example:
https://fotbalunas.cz/soutez/438/ means the ID of this league is 438.

Run the file scraper.py 

  - with arguments: `python3 scraper.py [-l ID]`
  - or without, and you'll be interactively prompted for the league ID: `python3 scraper.py`
  
After successful download, a new folder in your directory is created. Inside are two JSON files. One with basic info, second with all scraped games.


## Improvements and errors

This version of the program downloads only previous matches. The upcoming games and matches with the unclear result are skipped.
If you start the program with the same league number, it starts scraping all over and all JSON files for the league will be overwritten.
In future updates, I plan to scrap only not saved games and UPDATE JSON, not overwrite all in JSON file. 


I created this project for my home league, where it fits my needs perfectly. I tested it for other 10 leagues and fixed all the bugs I found.

In some lower leagues it can happen that line ups are missing or there is a mistake in the lineup. In such case I decided to inform user about the mistake and download all other info except the lineup of the team.

<img width="798" alt="1" src="https://user-images.githubusercontent.com/78157639/140912271-56d5cbf8-84e3-4ca0-933c-28f4fcaf7c42.png">


If you find a league with Uknown error, or a league which causes the program to crash, please let me know and I will try to fix it.

<img width="798" alt="Unkwown err" src="https://user-images.githubusercontent.com/78157639/140912286-5974ca3c-f0da-4bd0-8477-443ebbf19fbd.png">
