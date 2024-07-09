# DASHBOARD: streamlit app to display, compare and track IG account data
# RUNNER: runs the api and updates the database

import requests
import json

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def userInfo(target_username, file_id):

    url = "https://rocketapi-for-instagram.p.rapidapi.com/instagram/user/get_info"

    payload = { "username": target_username }
    headers = {
        "x-rapidapi-key": "ea15dbbb76msh4da275ec2164a97p1a5cedjsn2dd59ce2b3d8",
        "x-rapidapi-host": "rocketapi-for-instagram.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    save_file = open(file_id+".json", "w")
    json.dump(response.json(), save_file, indent = 6)
    save_file.close()
    return response.json()

# Get user_id from username
def instagramID_API(target_username):

    # extract user's id from the API response 
    # response = userInfo(target_username, file_id=target_username)
    f = open(target_username+'.json')
    response = json.load(f)
    target_id = response['response']['body']['data']['user']['id']

    # add matching ID & USERNAME to export table
    df_list = [[target_username, target_id]]
    df      = [[target_username, target_id]]

    # convert export table to pandadataframe then dict
    df = pd.DataFrame(df, columns = ['ig_username','ig_user_id'])
    print(df)

    # Convert DataFrame to list of dictionaries
    data = df.to_dict('records')

    # upsert to table: instagram_roster
    table_name = "social_roster"
    response = supabase.table(table_name).upsert(
        data,
        on_conflict="ig_username"
    ).execute()

    # output simpler list
    return df_list

# DATA SCRAPER CALL
# > needs to know which account
# > needs to know which posts (from what date, which is the limit post)

scrape_posts_after_id   = ''
scrape_posts_after_date = ''
scrape_posts_from_account = ''


# DATA SCRAPER from IG
# connects to the API
# imports data as JSON
# converts to CSV
# updates data in the database



# define username to extract ID for 
target_username = 'garyvee'

df = []
df += instagramID_API(target_username)