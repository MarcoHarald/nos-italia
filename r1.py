# DASHBOARD: streamlit app to display, compare and track IG account data
# RUNNER R1: runs the api and updates the database

import requests
from datetime import datetime
import json
from scraper import scrapeAccountPosts
from imageArchiver import uploadImage

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

# API Call on profile info: Get user_id from username
def userInfo(target_username, file_id):

    url = "https://rocketapi-for-instagram.p.rapidapi.com/instagram/user/get_info"

    payload = { "username": target_username }
    headers = {
        "x-rapidapi-key": "ea15dbbb76msh4da275ec2164a97p1a5cedjsn2dd59ce2b3d8",
        "x-rapidapi-host": "rocketapi-for-instagram.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    # change file name: username to ig_id
    # target_id = (response.json())['response']['body']['data']['user']['id']
    
    save_file = open(target_username+".json", "w")
    json.dump(response.json(), save_file, indent = 6)
    save_file.close()
    return response.json()

# Get user_id from username
def instagramID_API(target_username):

    # extract user's id from the API response 
    response = userInfo(target_username, file_id=target_username)
    f = open(target_username+'.json')
    response = json.load(f)
    target_id = response['response']['body']['data']['user']['id']

    # add matching ID & USERNAME to export table
    df_list = [[target_username, target_id]]
    df      = [[target_username, target_id]]

    # convert export table to pandadataframe then dict
    df = pd.DataFrame(df, columns = ['ig_username','ig_user_id'])

    # Convert DataFrame to list of dictionaries
    data = df.to_dict('records')

    # upsert to table: instagram_roster
    table_name = "social_roster"
    response = supabase.table(table_name).upsert(
        data,
        on_conflict="ig_username"
    ).execute()

    # output simpler list
    print('ID Fetcher:', df_list[0])
    return df_list

# DATA SCRAPER CALL
# > needs to know which account
# > needs to know which posts (from what date, which is the limit post)
scrape_posts_after_id   = ''
scrape_posts_after_date = ''
scrape_posts_from_account = ''



# TODO: check if username is in the supabase database

target_usernames = ['globalbiorev'] # define username to extract ID for 
# target_usernames = [] # NOTE: use blank list for cached data
df_usernames_ids = [] # New unsernames, from which to extract user IDs

for target_username in target_usernames:
    df_usernames_ids += instagramID_API(target_username)

# puts username IDs into a nice format
username_ids = pd.DataFrame(df_usernames_ids, columns = ['ig_username','ig_user_id'])
print('Scraping IG Accounts:',username_ids)

# DATA SCRAPER from IG: connects to the API, imports data as JSON, converts to CSV, updates data in the database.
for selected_account in df_usernames_ids:
    # scrape accounts
    print('----- Scraping & uploading:', selected_account[0])
    account_posts = scrapeAccountPosts(selected_account=selected_account, num_scrapes=2, post_max_id=0, label="zulu02")

    # upsert to table: instagram roster
    data = account_posts.to_dict('records')     # Convert DataFrame to list of dictionaries
    response = supabase.table(table_name="instagram").upsert(data, on_conflict="post_code").execute() 

    # DEBUG
    print("Post details updated:", response.count)

    # TODO: add max_id for each user, so that the next query will be lighter

# IMAGE CACHER: save cover images to the database 
# extract image link
# select username, post date after certain date,
    
# Convert the date string to a datetime object
filter_date = datetime.strptime("26/04/2024", "%d/%m/%Y")
table_name = "instagram"
platform = "Instagram"
author_name = "Global Biotech Revolution"

# Fetch data from Supabase
response = supabase.table(table_name).select("*").eq("platform", platform).eq("author_name", author_name).gte("post_date", filter_date.isoformat()).execute()
data = pd.DataFrame(response.data)  # convert response to managable pandas 

# data = data.reset_index()
print(data.head)

for index, row in data.iterrows():
    # save image to database, rename, add image name to the DB
    print('-----')
   
    image_link = row['media_image']  
    file_name = row['post_code']
    bucket_name = 'social_bucket'

    uploadImage(image_link, file_name, bucket_name)







