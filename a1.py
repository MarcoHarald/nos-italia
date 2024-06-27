import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def summaryStats(df):
    summaryStats = []

    # count number of posts
    numPosts = len(df.index)
    summaryStats += [["# posts", numPosts]]

    # average number of likes
    avgLikes = df['like_count'].sum()/numPosts
    summaryStats += [["# avg. likes", avgLikes]]

    # average number of comments
    avgComments = df['comment_count'].sum()/numPosts
    summaryStats += [["# avg. comments", avgComments]]

    # combine all summary stats into a table
    df_summaryStats = pd.DataFrame(summaryStats, columns=["data","#"])
    return df_summaryStats

def topPosts(df):
    # display top five performing posts with link, likes, type#EXPANSION: using hyperlink, include cover image of post

    # rank posts by likes
    df = df.sort_values('like_count', ascending=False)

    # trim list to only include top five
    df = df[['author','post_format','like_count','comment_count','post_code']]

    # only display link, likes, type, preview of image!!

    return df



st.title("Social View")
st.text("Browse social media performance of various instagram accounts")

# import file
df = pd.read_csv("o_NOS.csv")

# plot table with all data. Display only certain columns
st.dataframe(df, use_container_width=True)


# Summary stats
# show total number of posts
st.title("Summary Stats")
st.text("Number of posts, average likes per post")
st.dataframe(summaryStats(df), use_container_width=True)


# Top performing posts
st.title("Top Performing Posts")
st.dataframe(topPosts(df).head(5), use_container_width=True)

# pie chart by post type
df_pie = df.groupby(['post_format']).count()
df_pie = df_pie['post_code']
st.dataframe(df_pie, use_container_width=True)

# Pie Chart
st.subheader("Pie Chart")
pie_chart_data = df_pie
plt.pie(pie_chart_data['post_code'], labels=pie_chart_data['post_format'])
st.pyplot( plt )



