import json
from datetime import datetime
import pandas as pd
import requests


def list_posts(id, count, max_id,file_id):
    # import list of posts in blocks of 50
    # find user ID using this URL https://www.instagram.com/web/search/topsearch/?query=therock

    url = "https://rocketapi-for-instagram.p.rapidapi.com/instagram/user/get_media"

    payload = {
        "id": id,
        "count": count,
        "max_id": max_id
    }
    headers = {
        "x-rapidapi-key": "ea15dbbb76msh4da275ec2164a97p1a5cedjsn2dd59ce2b3d8",
        "x-rapidapi-host": "rocketapi-for-instagram.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    save_file = open(file_id+".json", "w")
    json.dump(response.json(), save_file, indent = 6)
    save_file.close()

    # print(response.json())
    return response.json()

# TL:DR   Extract comment, like and caption from JSON and add it all to an array
def load_post_details(filename):

    with open(filename) as f:
        d = json.load(f)

    # select the posts to read through
    items = d["response"]["body"]["items"]
    post_account = d["response"]["body"]["user"]["full_name"]

    # save file items
    df = []

    for item in items:
        # author name
        author_name = item["user"]["full_name"]
        author_name = post_account

        # save post code
        post_code = item["code"]
        print("Working on...",post_code)

        # save post URL
        post_url = "https://www.instagram.com/p/"+post_code+"/"

        # post format
        post_format = item["product_type"]

        # save caption
        try:
            caption_content = item["caption"]["text"]
        except:
            caption_content = ""

        # device timestamp
        timestamp = str(item["taken_at"])
        timestamp = int(timestamp) #int(timestamp[:10])
        post_date = datetime.utcfromtimestamp(timestamp).strftime('%Y/%m/%d')

        # save like count
        like_count = item["like_count"]

        # save comment count
        comment_count = item["comment_count"]

        # co-author production
        try:

            # add all co-authors
            co_authors = ""
            for author in item["coauthor_producers"]:
                co_authors = co_authors+"@"+author["username"]+" "

            # if original author is not the selected account, append original author as co-author
            original_author = item["user"]["username"]
            selected_author = d["response"]["body"]["user"]["username"]
            if original_author != selected_author:
                co_authors = co_authors+"@"+original_author+", "

        except:
            co_authors = item["invited_coauthor_producers"]

        # platform where content is published
        platform = "Instagram"

        # profile pic url
        profile_pic_url = d["response"]["body"]["user"]["profile_pic_url"]

        # media type (video or image)
        media_format = item["media_type"]

        # media is image, only save image
        if media_format == 1:
            media_image = item["image_versions2"]["candidates"][0]["url"]
            media_first_frame = ""
            video_length = ""
            video_file_url = ""
            video_views = ""

        # media is video, save details
        elif media_format ==2: 
            media_image = item["image_versions2"]["candidates"][0]["url"]
            media_first_frame = item["image_versions2"]["additional_candidates"]["first_frame"]["url"] 
            video_length =  item["video_duration"]
            video_file_url =  item["video_versions"][0]["url"]
            video_views =  item["play_count"]
        
        # catch unexpected media types and report them to user
        else:
            print("Different media format:", media_format)
            media_image = item["image_versions2"]["candidates"][0]["url"]
            media_first_frame = ""
            video_length = ""
            video_file_url = ""
            video_views = ""       

        post_details =  [author_name, post_date, post_code, post_format, like_count, comment_count, video_views, caption_content, co_authors, media_format, media_image, media_first_frame, video_length, video_file_url,profile_pic_url, platform]
        df.append(post_details)

    return df

# CREATE API CALLS and SAVE DATA TO FILE
def run_api_series(account, id, max_id, search_count, count, label):
    for i in range(search_count):

        # setup filesaves and run API call
        file_id = label + "_" + account + "_" + str(i)
        post_list = list_posts(int(id), count, max_id, file_id)


        # API tells us whether there are more posts to scrape
        print("More posts to scrape:", post_list["response"]["body"]["more_available"])

        # check that there are more posts to scrape
        if post_list["response"]["body"]["more_available"] == True:
            max_id = post_list["response"]["body"]["next_max_id"]
            print("Retrieving posts #", file_id, "up to post", max_id)

        # Adjust number of files to match how many exports have been made
        else:
            print("Finished search at", i)
            search_count = i
            break
    return post_list

# COMBINE all data files into one
def combine_account_files(selected_accounts):
    appended_data = []

    for selected_account in selected_accounts:
        import_file = pd.read_csv("o_"+selected_account[0]+".csv")
        appended_data.append(import_file)
    
    appended_data = pd.concat(appended_data)
    return appended_data

# MEGA SCRAPER FUNCTION    
def scrapeAccountPosts(selected_account, num_scrapes, post_max_id, label):
    
    # selected_account : details of the IG account to retrieve posts from
    # num_scrapes : # how many re-runs of the API call to retrieve more posts
    # post_max_id : to avoid re-scraping same posts, API returns a max_id of last scraped post
    # label : label the JSON & output files with a unique identifier. Avoid overwriting and losing data. 

    # setup API call to read files
    account = selected_account[0]
    id = selected_account[1]
    print("API CALL for:", account, id)

    # setup API parameters
    count = 50 # max number of posts to scrape at a time
    max_id = 0 # to avoid re-scraping same posts, API returns a max_id of last scraped post
    search_count = num_scrapes # how many re-runs of the API call to retrieve more posts

    # CREATE API CALLS and SAVE DATA TO FILE
    run_api_series(account, id, max_id, search_count, count, label)
    # print("Skipping API. Using cached data.")

    # RECREATE LIST OF SAVED FILES TO READ FROM
    files = []
    for i in range(search_count):
        files += [label+"_"+account+"_"+str(i)+".json"]


    # LOAD IN DATA FROM SAVEFILES and LOAD INTO A UNIFIED TABLE
    post_details = []

    for filename in files:

        # Select file to load and import
        try:
            current_post_details = load_post_details(filename)
            print("Imported saved data:",filename)
            # append data into single output table
            post_details += current_post_details

        except:
            print("Savefile not found:", filename)

    # save data into a dataframe and export
    df = pd.DataFrame(post_details, columns =  ['author_name', 'post_date', 'post_code', 'post_format', 'like_count', 'comment_count', 'video_views', 'caption_content', 'co_authors', 'media_format', 'media_image', 'media_first_frame', 'video_length', 'video_file_url','profile_pic_url', 'platform'])

    df.to_csv("o_"+label+"_"+account+".csv")
    print("Scraped posts for ", "o_"+label+"_"+account+".csv")
    return(df)

# MEGA SCRAPER FUNCTION using cached files
def scrapeAccountPostsCached(selected_account, num_scrapes, post_max_id, label):
    
    # selected_account : details of the IG account to retrieve posts from
    # num_scrapes : # how many re-runs of the API call to retrieve more posts
    # post_max_id : to avoid re-scraping same posts, API returns a max_id of last scraped post
    # label : label the JSON & output files with a unique identifier. Avoid overwriting and losing data. 

    # setup API call to read files
    account = selected_account[0]
    id = selected_account[1]
    print("API CALL for:", account, id)

    # setup API parameters
    count = 50 # max number of posts to scrape at a time
    max_id = 0 # to avoid re-scraping same posts, API returns a max_id of last scraped post
    search_count = num_scrapes # how many re-runs of the API call to retrieve more posts

    # CREATE API CALLS and SAVE DATA TO FILE
    # run_api_series(account, id, max_id, search_count, label)
    print("Skipping API. Using cached data.")

    # RECREATE LIST OF SAVED FILES TO READ FROM
    files = []
    for i in range(search_count):
        files += [label+"_"+account+"_"+str(i)+".json"]


    # LOAD IN DATA FROM SAVEFILES and LOAD INTO A UNIFIED TABLE
    post_details = []

    for filename in files:

        # Select file to load and import
        try:
            current_post_details = load_post_details(filename)
            print("Imported saved data:",filename)
            # append data into single output table
            post_details += current_post_details

        except:
            print("Savefile not found:", filename)

    # save data into a dataframe and export
    df = pd.DataFrame(post_details, columns =  ['author_name', 'post_date', 'post_code', 'post_format', 'like_count', 'comment_count', 'video_views', 'caption_content', 'co_authors', 'media_format', 'media_image', 'media_first_frame', 'video_length', 'video_file_url','profile_pic_url', 'platform'])

    df.to_csv("o_"+label+"_"+account+".csv")
    print("Scraped posts for ", "o_"+label+"_"+account+".csv")
    return(df)



# FIND ACCOUNT ID: https://www.instagram.com/web/search/topsearch/?query=legaofficial
IG_accounts = []
IG_accounts += [['Lega', 8720216241]]
IG_accounts += [['FDI',  276272006]]
IG_accounts += [['PD',   519535327]]
IG_accounts += [['AVS',  54849421205]]
IG_accounts += [['M5S',  1275108972]]
IG_accounts = [['NOS',  61786487814]]


# EXAMPLE CODE RUN OF THIS SCRIPT
if 1 == 2:

    # scrape & save all the instagram posts of these accounts
    for selected_account in IG_accounts:
        scrapeAccountPosts(selected_account=selected_account, num_scrapes=10, post_max_id=0, label="zulu01")

    # combine all account files into one
    print("Saving data to single file...")
    df_all = combine_account_files(IG_accounts)
    df_all.to_csv("o_allData.csv")

