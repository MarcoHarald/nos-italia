import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import dateutil.parser as parser
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)


# Filter Button Function. Call as a DF to apply filter functionality.
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

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
    df = df[['author_name','post_format','like_count','comment_count','post_code']]

    # only display link, likes, type, preview of image!!

    return df

# filter by top Performing Posts
def featuredPosts(df, post_week):
    featured_posts = df
    # rank posts by number of likes
    featured_posts = featured_posts.sort_values(by="like_count", ascending=False)
    # filter posts by chosen week 
    featured_posts = featured_posts[featured_posts["post_week"]==post_week]
    # filter by top20
    featured_posts = featured_posts.head(20)

    # EXPANSIONS: rank engagement rate
    return featured_posts

st.title("Social View ")
st.text("Browse social media performance of various instagram accounts")


# IMPORT DATA
# uploaded_file = st.file_uploader("Carica il tuo file qui")
df = pd.read_csv("o_allData.csv")

# plot table with all data. Display only certain columns
st.dataframe(df, use_container_width=True)


# SUMMARY STATS
# show total number of posts
st.title("Summary Stats")
st.text("Number of posts, average likes per post")
st.dataframe(summaryStats(df), use_container_width=True)

# Top performing posts
st.title("Top Performing Posts by NOS")
st.dataframe(topPosts(df[df['author_name']=='Nos']).head(5), use_container_width=True)


# Post Volumes
# group dates by weeknumber. Read date using parse.
st.title("Ritmo di Pubblicazione")
df['post_week'] = df['post_date'].apply(lambda x: parser.parse(x, dayfirst=True).isocalendar()[1])

# group by Weeknum & author, count, then only select the relevant columns
col_toGroupBy = ['post_week','author_name']
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



# TOP PERFORMING POSTS
st.title('Top Performing Content')
featured_posts = featuredPosts(df,post_week=22) # filter function. Filters by week, like_count, top20.

# Import image from this URL format: https://www.instagram.com/p/CQX8lKutaZU/media/?size=l
image_links = 'https://www.instagram.com/p/' + featured_posts['post_code'].astype(str)+"/media/?size=l"
like_data = featured_posts['like_count']

# Setup grid to place images
n_pics = 20 # images to display
n_cols = 3 # images per row 
n_rows = int(1+n_pics // n_cols) # calculate number of rows
rows = [st.columns(n_cols) for _ in range(n_rows)] # define row IDs
cols = [column for row in  rows for column in row] # define col IDs
for col, image, likes in zip(cols, image_links, like_data): # loop through rows and select image
    col.image(image)
    col.text((str(round(likes/1000.0,1))+"k likes"))

# print table for reference
st.dataframe(featured_posts)


# FILTER THROUGH ALL POSTS
# Apply filter functionality to DB
st.title("Filter Database")
df_filter = df[["author_name","post_format","like_count","comment_count","post_code"]]
st.dataframe(filter_dataframe(df_filter))











# ARCHIVE datetime
# datetime.date(2010, 6, 16).isocalendar()[1]
# >>>date = datetime.strptime('Thu, 16 Dec 2010 12:14:05', '%a, %d %b %Y %H:%M:%S')
# date = parser.parse(df_calendar.iloc[1,0],dayfirst=True)
# weeknum = date.isocalendar()[1] 
