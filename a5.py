# DASHBOARD: streamlit app to display, compare and track IG account data
# RUNNER: runs the api and updates the database

import streamlit as st
import datetime
from datetime import datetime, timedelta
import pandas as pd
import subprocess
import time
from r1 import runInstagramScraper
import plotly.express as px
from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client 
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Fetch data from Supabase
def fetch_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    data = pd.DataFrame(response.data)
    return data

# Helper functions
def get_stats(data, author_name):
    author_data = data[data['author_name'] == author_name]
    num_posts = len(author_data)
    avg_like_count = author_data['like_count'].mean()
    avg_comment_count = author_data['comment_count'].mean()
    engagement_rate = avg_comment_count + avg_like_count
    return num_posts, avg_like_count, avg_comment_count, engagement_rate

def get_top_posts(data, author_name):
    author_data = data[data['author_name'] == author_name]
    top_posts = author_data.sort_values(by='like_count', ascending=False)
    return top_posts

# Display the top posts in a three-column grid
def grid(data, n_cols):
    # Setup grid to place images
    top_posts = data
    n_pics = 20 # images to display
    n_cols = n_cols # images per row 
    n_rows = int(1+n_pics // n_cols) # calculate number of rows
    rows = [st.columns(n_cols) for _ in range(n_rows)] # define row IDs
    cols = [column for row in  rows for column in row] # define col 

    for col, post_code, post_image, like_count, comment_count, author_name in zip(cols, top_posts['post_code'], top_posts['saved_cover_image'], top_posts['like_count'], top_posts['comment_count'], top_posts['author_name']): # loop through rows and select image
        # post_image_link = 'https://www.instagram.com/p/' + post_code +"/media/?size=l"
        post_image_link = post_image
        col.image(post_image_link)
        col.write(f"Likes: {str(round(like_count/1000.0,1))} k")
        col.write(f"Comments: {comment_count}")
        engagement_rate = (like_count + comment_count) 
        col.write(f"Engagement Rate: {engagement_rate/1000.0:.0f} %")
        col.write(f"Author: {author_name}")        
        col.write(f"[View on Instagram]({post_code})")

def grid_stacked(top_posts):
    cols = st.columns(3)
    for i, row in top_posts.iterrows():
        with cols[i % 3]:
            post_image_link = 'https://www.instagram.com/p/' + row['post_code']+"/media/?size=l"
            st.image(post_image_link)
            st.write(f"Author: {row['author_name']}")
            st.write(f"Likes: {row['like_count']}")
            st.write(f"Comments: {row['comment_count']}")
            engagement_rate = (row['like_count'] + row['comment_count']) / (row['like_count'] + row['comment_count'])
            st.write(f"Engagement Rate: {engagement_rate:.2f}")
            st.write(f"[View on Instagram]({row['post_code']})")
 
def groupby_author(data):
    # Assuming your DataFrame is named 'df'
    grouped_df_author = data.groupby('author_name').agg({
        'like_count': 'mean',
        'comment_count': 'mean',
        'post_code': 'count'
    }).reset_index()

    # Rename the columns for clarity
    grouped_df_author.columns = ['author_name', 'avg_like_count', 'avg_comment_count', 'post_count']
    return grouped_df_author

# Calculate first day of a week number
def get_date_of_week(year, week):
    first_day_of_year = datetime(year, 1, 1)
    first_monday = first_day_of_year + timedelta(days=(7 - first_day_of_year.weekday()))
    target_date = first_monday + timedelta(weeks=week-1)
    return target_date.strftime("%Y-%m-%d")

# Slider feature to select range of weeks, returns filtered data  
def weekSlider(df):

    # Get the minimum and maximum week numbers from your data
    min_week = df['week_number'].min()
    max_week = df['week_number'].max()
    
    max_week = 29    # OVERRIDE TO CURRENT WEEK

    # Assuming the data is from the current year
    current_year = datetime.now().year

    # Create a slider for week range selection
    start_week, end_week = st.slider(
        "Select Week Range",
        min_value=int(min_week),
        max_value=int(max_week),
        value=(int(min_week), int(max_week))
    )

    # Display the date range
    start_date = get_date_of_week(current_year, start_week)
    end_date = get_date_of_week(current_year, end_week)
    # st.write(f"Selected date range: {start_date} to {end_date}")

    # Filter the dataframe based on the selected week range
    df_filtered = df[(df['week_number'] >= start_week) & (df['week_number'] <= end_week)]
    return df_filtered

# Index post performance against lifetime (divides each post by the account avg., grouped by week)
def get_author_summary(df):
    # Group by author and week
    grouped = df.groupby(['author_name', 'week_number'])
    
    # Calculate summary statistics
    summary = grouped.agg({
        'author_name': 'count',
        'like_count': ['sum', 'mean']
    }).reset_index()
    
    # Rename columns
    summary.columns = ['author_name', 'week_number', 'post_count', 'total_likes', 'avg_likes_per_post']
    
    # Calculate lifetime average likes per post for each author
    lifetime_avg = df.groupby('author_name')['like_count'].mean().reset_index()
    lifetime_avg.columns = ['author_name', 'lifetime_avg_likes']
    
    # Merge summary with lifetime average
    summary = pd.merge(summary, lifetime_avg, on='author_name')
    
    # Calculate indexed likes per post
    summary['indexed_likes_per_post'] = summary['avg_likes_per_post'] / summary['lifetime_avg_likes']
    
    # Reorder columns
    summary = summary[['author_name', 'week_number', 'post_count', 'avg_likes_per_post', 'indexed_likes_per_post']]
    
    return summary

# filter data to between specified dates, returns filtered data    
def filterByDate(data, earliest_date, lastest_date):
    earliest_date = '1/1/2024'
    latest_date = '13/07/2024'

    # Convert the string to a datetime object
    date_object_1 = datetime.strptime(earliest_date, "%d/%m/%Y")
    date_object_2 = datetime.strptime(latest_date, "%d/%m/%Y")

    # Convert the datetime object to the desired format
    formatted_date_1 = date_object_1.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    formatted_date_2 = date_object_2.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    data = data[(data['post_date'] >= formatted_date_1) & (data['post_date'] <= formatted_date_2)]
    return data


def fetchAccountButton():
        # Instagram username input and button
    instagram_username = st.text_input("Enter Instagram username (without @)")
    if st.button("Fetch Instagram Data"):
        if instagram_username:
            with st.spinner(f"Fetching data for @{instagram_username}... This may take about 20 seconds."):
                progress_bar = st.progress(0)
                for i in range(20):
                    time.sleep(0.2)  # Simulate work being done
                    progress_bar.progress(i + 1)
                result = runInstagramScraper(instagram_username)
                st.success(f"Data fetched for @{instagram_username}")
                st.text(result)  # Display the result or message from the script
        else:
            st.warning("Please enter an Instagram username")

    return instagram_username
def fetchAccountSidebar():
  # Sidebar for Instagram data fetching
    st.sidebar.header("Fetch Instagram Data")
    instagram_username = st.sidebar.text_input("Enter Instagram username (without @)")
    fetch_button = st.sidebar.button("Fetch Instagram Data")

    if fetch_button:
        if instagram_username:
            with st.sidebar:
                with st.spinner(f"Fetching data for @{instagram_username}... This may take about 60 seconds."):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.6)  # Simulate work being done
                        progress_bar.progress(i + 1)
                    result = runInstagramScraper(instagram_username)
                    st.success(f"Data fetched for @{instagram_username}")
                    st.text_area("Script Output", result, height=200)  # Display the result or message from the script
        else:
            st.sidebar.warning("Please enter an Instagram username")


# Import data to app
data = pd.read_csv('o_allData.csv')
data = fetch_data('instagram')

# Streamlit App
st.title("Social Media Performance Tracker")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Key Stats", "Trends", "See your insta"])

# Page One
if page == "Key Stats":
    
    st.header("IG Account Statistics")
    
    # Dropdown menu to select author
    author_names = data['author_name'].unique()
    author_name = st.selectbox("Select Author", author_names)
    
    num_posts, avg_like_count, avg_comment_count, engagement_rate = get_stats(data, author_name)
    
    st.metric("Number of Posts", num_posts)
    st.metric("Average Likes per Post", f"{avg_like_count:.0f}")
    st.metric("Average Comments per Post", f"{avg_comment_count:.0f}")
    st.metric("Average Engagement Rate", f"{engagement_rate:.0f}")
   
   
    st.header("Top Posts of the Week")
    top_posts = get_top_posts(data, author_name)
    grid(top_posts, 3) # setup grid with posts

    

# Page Two
if page == "Trends":
    st.header("Key Stats Over Time")
    
    df = data
    author_names = data['author_name'].unique()    # unique list of account names for the selector
    data = data.sort_values(by=['post_date'])     # order data by date so it doesn't go jagged
    data['post_date'] = pd.to_datetime(data['post_date'])  # convert timestamps into datetime objects for python
    data['week_number'] = data['post_date'].dt.isocalendar().week

    # FILTER AUTHOR ACCOUNTS
    # Create a multiselect widget for author selection
    selected_authors = st.multiselect('Select authors:', author_names)

    # Filter the DataFrame based on selected authors
    if selected_authors:
        data = data[data['author_name'].isin(selected_authors)]
    else:
        data = data


    # FILTER DATES
    data = weekSlider(data)

    # GROUP BY WEEK & AUTHOR
    # Assuming your DataFrame is named 'df'
    grouped_df_AW = data.groupby(['author_name', 'week_number']).agg({
        'like_count': 'mean',
        'comment_count': 'mean',
        'post_code': 'count'
    }).reset_index()

    # Rename the columns for clarity
    grouped_df_AW.columns = ['author_name', 'post_date', 'like_count', 'comment_count', 'post_count']

    # Indexing post performance: has an account outperformed themselves on a particular week?
    indexed_performance = get_author_summary(data)


    # ASSIGN WHAT TO PLOT
    data = grouped_df_AW

    # Plotting data over time
    fig = px.line(data, x='post_date', y='like_count', color='author_name', title='Average Likes Over Time')
    st.plotly_chart(fig)

    fig = px.line(data, x='post_date', y='comment_count', color='author_name', title='Average Comments Over Time')
    st.plotly_chart(fig)

    #    fig = px.line(data, x='post_date', y=(data['like_count'] + data['comment_count']) / data['like_count'].count(), color='author_name', title='Engagement Rate Over Time')
    #    st.plotly_chart(fig)

    fig = px.line(indexed_performance, x='week_number', y=indexed_performance['indexed_likes_per_post'], color='author_name', title='Account Performance')
    st.plotly_chart(fig)


    st.header("Top Posts of the Week")
    author_name = st.selectbox("Select Author", author_names)
    top_posts = get_top_posts(df, author_name)
    grid(top_posts.head(30), n_cols=3)

    #  __name__ == "__main__":
    #    st.run()


# Page Three
if page == "See your insta":
    fetchAccountButton()

    # Add account:
    # fetchAccountSidebar()
