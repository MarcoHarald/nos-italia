import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import dateutil.parser as parser

# create a table with number of posts, avg likes, comments 
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

# create a table ranked by the most liked post
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
# uploaded_file = st.file_uploader("Carica il tuo file qui")
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


# Post Volumes
# group dates by weeknumber. Read date using parse.
st.title("Ritmo di Pubblicazione")
df['post_week'] = df['post_date'].apply(lambda x: parser.parse(x, dayfirst=True).isocalendar()[1])

# group by Weeknum & author, count, then only select the relevant columns
col_toGroupBy = ['post_week','author']
df_calendar = df.groupby(col_toGroupBy).count().reset_index().rename(columns={'Unnamed: 0':'count'})[col_toGroupBy+['count']]
st.line_chart(df_calendar, x=col_toGroupBy[0], y='count', color=col_toGroupBy[1])


# Post formats: reels, single post, carousels.
st.title("Posts Formats")
st.subheader("Post Formats")
pie_chart_data = df.groupby(['post_format']).count()['post_code'].reset_index()
plt.pie(pie_chart_data['post_code'], labels=pie_chart_data['post_format'])
st.pyplot( plt )
st.dataframe(pie_chart_data, use_container_width=True)

# Bar Chart
st.subheader("Post Formats")
bar_chart_data = df.groupby(['post_format']).count()['post_code'].reset_index()
st.bar_chart(bar_chart_data, x='post_format', y='post_code')
st.dataframe(bar_chart_data, use_container_width=True)











# ARCHIVE datetime
# datetime.date(2010, 6, 16).isocalendar()[1]
# >>>date = datetime.strptime('Thu, 16 Dec 2010 12:14:05', '%a, %d %b %Y %H:%M:%S')
# date = parser.parse(df_calendar.iloc[1,0],dayfirst=True)
# weeknum = date.isocalendar()[1] 
