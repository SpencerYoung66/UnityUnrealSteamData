# -*- coding: utf-8 -*-
"""WebScrapperUnityUnrealSteam.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wHpA57G8t14h1SCRNC84vFnn6WJySIW1
"""

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import time

# Get the Unity game list from Wikipedia, convert to Beautiful Soup object

url = 'https://en.wikipedia.org/wiki/List_of_Unity_games'
unityr = requests.get(url)
unitysoup = BeautifulSoup(unityr.text)

# Games are all part of Unordered Lists
unityullist = unitysoup.find_all("ul")

# 1 - 17 are the lists
gamelist = []
for i in range(0, 17):
  # Games are all hyperlinks
  for text in unityullist[i+1].find_all("a"):
    # Some links are just hyperlinks with the following format "[number]" or say citation needed, 
     # remove these
    if bool(re.match("\[\d+\]", text.text)) or text.text == "citation needed":
      continue
    # Change to lowercase to avoid case differences later
    gamelist.append(text.text.lower())

print(len(gamelist))

# Get list of all apps in Steam store, giant list
url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json"
r = requests.get(url)

# Convert to dictionary
unitygamesdict = r.json()

# Comes as a three-stacked list (dict, list, list), loop through to inner dictionary and 
 # convert to dictionary
for lielement in unitygamesdict["applist"]["apps"]:
  lielement = dict(lielement)

# Create list of game titles from Steam
steamgamelist = []
for i in range(len(unitygamesdict["applist"]["apps"])):
  # Lower case so that easier to compare to Wikipedia list
  steamgamelist.append(unitygamesdict["applist"]["apps"][i]["name"].lower())

# Convert to sets, do intersection to get all of the same games, convert back to list
gamelist = list(set(gamelist) & set(steamgamelist))

len(gamelist)

# Get tables from Unreal list, convert to Beautiful Soup
url = 'https://en.wikipedia.org/wiki/List_of_Unreal_Engine_games'
unrealdflist = pd.read_html(url)
# unrealr = requests.get(url)
# unrealsoup = BeautifulSoup(unrealr.text)

# Initialize as blank, then loop through and combine tables from different years into one dataframe
unrealdf = None
for i in range(1, 7):
  if unrealdf is None:
   unrealdf = unrealdflist[i]
  else:
    unrealdf = unrealdf.append(unrealdflist[i], ignore_index = True)

# Erase null Platforms
unrealdf = unrealdf[unrealdf["Platform"].notnull()]

# Only get the games released on Steam
unrealdf = unrealdf[unrealdf["Platform"].str.contains("Microsoft Windows")]

# Get rid of games that haven't Released
unrealdf = unrealdf[unrealdf["Year"] != "TBA"]

# Get rid of games that haven't Released
unrealdf = unrealdf[unrealdf["Year"] != "2023"]

unrealdf = unrealdf.reset_index()

# Lower case for easier comparison
unrealdf["Title"] = unrealdf["Title"].str.lower()

for i in range(len(unrealdf)):
  # Clean the titles, have one to many links, get rid of them
  if bool(re.match(".*\[\d+\]", unrealdf["Title"].iloc[i])):
    unrealdf["Title"].iloc[i] = unrealdf["Title"].iloc[i].split("[")[0]

# Intersection between Unreal and steam games
unrealgamelist = list(set(steamgamelist) & set(unrealdf["Title"]))
unrealgamelist

# Concatenate Unity games and Unreal games
gamelist = gamelist + unrealgamelist

len(gamelist)

# Initialize blank list of appids as long as games
appidlist = [None] * len(gamelist)

# Loop through steam games and get Steam appid for game, put in identical index location as gamelist
for i in range(len(unitygamesdict["applist"]["apps"])):
  if unitygamesdict["applist"]["apps"][i]["name"].lower() in gamelist:
    appidlist[gamelist.index(unitygamesdict["applist"]["apps"][i]["name"].lower())] = unitygamesdict["applist"]["apps"][i]["appid"]

len(appidlist)

# Make DataFrame with Game Title and AppID
completedict = {"Game": gamelist, "AppID": appidlist}
completedf = pd.DataFrame(completedict)

# url = "https://store.steampowered.com/api/appdetails?appids=373700"
# r = requests.get(url)
# testjson = r.json()
# testjson["373700"]["success"]

# Get All rating info: Total ratings, positive ratings, negative ratings, review score, and review score description
# Wait 2 seconds between API calls
ratingsjsonlist = []
for i in range(len(completedf)):
  time.sleep(2)
  url = "https://store.steampowered.com/appreviews/" + str(completedf['AppID'].iloc[i]) + "?json=1&language=all"
  r = requests.get(url)
  ratingsjsonlist.append(r.json()['query_summary'])

len(ratingsjsonlist)

# Initialize Blank lists for rest of columns
reviewscore = []
positivereviews = []
negativereview = []
reviewscoredesc = []
totalreview = []
unitssold = []
engine = []

# Loop through ratings list, get all of the info for the rest of the dataframe, including adding the engine (Unreal or Unity)
for i in range(len(ratingsjsonlist)):
  if gamelist[i] in unrealgamelist:
    engine.append("Unreal Engine")
  else:
    engine.append("Unity Engine")
  reviewscore.append(ratingsjsonlist[i]['review_score'])
  positivereviews.append(ratingsjsonlist[i]['total_positive'])
  negativereview.append(ratingsjsonlist[i]['total_negative'])
  reviewscoredesc.append(ratingsjsonlist[i]['review_score_desc'])
  totalreview.append(ratingsjsonlist[i]['total_reviews'])
  unitssold.append(int(ratingsjsonlist[i]['total_reviews']) * 20)

# Add lists as columns
completedf['Review Score'] = reviewscore
completedf['Positive Reviews'] = positivereviews
completedf['Negative Reviews'] = negativereview
completedf['Review Score Description'] = reviewscoredesc
completedf['Total Review'] = totalreview
completedf['Units Sold (Estimated)'] = unitssold
completedf['Engine'] = engine

# Save DataFrame as csv
completedf.to_csv("Games.csv")