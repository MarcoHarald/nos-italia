# DASHBOARD: streamlit app to display, compare and track IG account data
# RUNNER: runs the api and updates the database

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

    for col, post_code, like_count, comment_count, author_name in zip(cols, top_posts['post_code'], top_posts['like_count'], top_posts['comment_count'], top_posts['author_name']): # loop through rows and select image
        post_image_link = 'https://www.instagram.com/p/' + post_code +"/media/?size=l"
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
 
# Import data to app
data = pd.read_csv('o_allData.csv')
data = fetch_data('instagram')

# Streamlit App
st.title("Social Media Performance Tracker")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Key Stats", "Trends"])

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
    st.write(top_posts)



# Page Two
if page == "Trends":
    st.header("Key Stats Over Time")
    
    author_names = data['author_name'].unique()



    # Plotting data over time
    fig = px.line(data, x='post_date', y='like_count', color='author_name', title='Average Likes Over Time')
    st.plotly_chart(fig)
    
    fig = px.line(data, x='post_date', y='comment_count', color='author_name', title='Average Comments Over Time')
    st.plotly_chart(fig)
    
    fig = px.line(data, x='post_date', y=(data['like_count'] + data['comment_count']) / data['like_count'].count(), color='author_name', title='Engagement Rate Over Time')
    st.plotly_chart(fig)
    
    st.header("Top Posts of the Week")
    author_name = st.selectbox("Select Author", author_names)
    top_posts = get_top_posts(data, author_name)
    grid(top_posts.head(30), n_cols=3)

#  __name__ == "__main__":
#    st.run()
