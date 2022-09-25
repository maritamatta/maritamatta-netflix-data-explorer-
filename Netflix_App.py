#Web App Library
import streamlit as st

#Data Manipulation Libraries
import pandas as pd
import numpy as np

#Country Manipulation Libraries
from dataprep.clean import validate_country
import pycountry_convert as pc

#Visualization Libraries
import plotly.graph_objs as go
import plotly.express as px


#SideBar Visual Selection
st.sidebar.title('What are you curious to know about Netflix?')
chart_visual = st.sidebar.selectbox("Select to get answers and insights", ("Select", "Type of Shows", "Ratings", "Shows in Continents", "Genres", "Shows over the years"))

#Setting Project Title
st.title('Netflix Data Exploration')

#Load the data
data = 'netflix_data.csv'
netflix_df = pd.read_csv(data)

#Fixing DataType: date_added is a datetime data type and not an object
netflix_df['date_added'] = pd.to_datetime(netflix_df['date_added'])

##For it to be clear and to create more visualizations we can split date_added to month_added and year_added
#Add month_added column
netflix_df['month_added'] = netflix_df['date_added'].dt.month_name()
#Add year_added column
netflix_df['year_added'] = netflix_df['date_added'].dt.year

#Ratings Dictionary based on target ages
ratings_ages = {
    'TV-PG': 'Older Kids',
    'TV-MA': 'Adults',
    'TV-Y7-FV': 'Older Kids',
    'TV-Y7': 'Older Kids',
    'TV-14': 'Teens',
    'R': 'Adults',
    'TV-Y': 'Kids',
    'NR': 'Adults',
    'PG-13': 'Teens',
    'TV-G': 'Kids',
    'PG': 'Older Kids',
    'G': 'Kids',
    'UR': 'Adults',
    'NC-17': 'Adults',
}
#Adding a target_ages column
netflix_df['target_ages'] = netflix_df['rating'].replace(ratings_ages)

##Add Country Code, Continent Code, and Continent Name¶
#By adding this we can compare the amount of shows based on continent instead of country. Hence, our visual will be easy to read without a huge amount of colors
netflix_df = netflix_df[validate_country(netflix_df['country'])]
netflix_df['country code'] = netflix_df['country'].apply(lambda x: pc.country_name_to_country_alpha2(x, cn_name_format = "default"))
netflix_df['continent code'] = netflix_df['country code'].apply(lambda x: pc.country_alpha2_to_continent_code(x))
netflix_df['continent name'] = netflix_df['continent code'].apply(lambda x: pc.convert_continent_code_to_continent_name(x))

#Fixing Column Names
rename_columns = {
    'country':'country name',
    'listed_in': 'genres'
}

netflix_df = netflix_df.rename(columns = rename_columns)  
#Fixing Column Order
netflix_df = netflix_df[['type', 'title', 'director', 'rating', 'target_ages', 'duration', 'release_year', 
                         'date_added', 'month_added', 'year_added', 'country name', 'continent name', 'genres']]

#Visualize our dataset on streamlit
st.markdown('Refer to the dataset:')
if st.checkbox('Show data'):
    st.subheader('Netflix dataset')
    st.write(netflix_df)

## Pie Chart showing the percentage amount of movies and TV Shows
if chart_visual == 'Type of Shows':
    st.subheader('Is there more movies than series?')
    show_type = go.Figure(data=[go.Pie(labels = netflix_df['type'].unique(),
                            values = netflix_df['type'].value_counts())])
    show_type.update_traces(textfont_size=15,
                 textinfo = 'label+percent',
                 marker=dict(line=dict(color='#000000', width=2)),
                 pull=[0, 0.1]
                 )
    show_type.update_layout(title="Type of Shows")
    show_type

    st.caption('We can see that there is 69% movies, and 31% TV Shows. Hence, There are much more movies than series.')

## Rating dataframe showing the amount of shows with its rating for each age target 
rating_df = netflix_df.groupby(['rating', 'target_ages'])[ 'target_ages'].count().reset_index(name='count').sort_values(['count'], ascending = False)

if chart_visual == 'Ratings':
        st.subheader('How does the rating differ based on every age category?')
        ratings = px.bar(rating_df, x='rating', y='count', color='target_ages', title="Rating Based on Target Ages")
        st.plotly_chart(ratings)
        st.caption("Adults has the largest amount of movies/series to entertain themselves compared to teens and kids. Also, Adults can watch whatever they want without restriction to ratings. Although Netflix is an app used more by adults and teenagers, the company can add more shows to the kids' section.")

#Country Dataframe showing the amount of shows added every year per continent 
country_df = netflix_df.groupby(['year_added', 'continent name', 'country name'])[ 'continent name'].count().reset_index(name='year_count').sort_values(by=['year_added', 'year_count'], ascending=False)
country_df = country_df.query('year_added >= 2015')

if chart_visual == 'Shows in Continents':
    st.subheader('Over the years, how many shows does every continent have?')
    ## Map showing the amount of shows over the years
    show_years = px.scatter_geo(country_df, locations='country name',
                    locationmode='country names',
                    animation_frame='year_added',
                    animation_group='continent name',
                    color='continent name',
                    hover_name='country name',
                    size='year_count',
                    size_max = 60,
                    opacity = 0.8,
                    projection='natural earth')

    show_years.update_layout(title_text='Amount of Shows Over the past 7 years in each Continent')
    st.plotly_chart(show_years)
    st.caption('By going through the years backwards, we can see that the number of shows added on netflix are slowly decreasing. Which means that the company is adding shows every year on the app. We can also notice the difference between 2015 and 2016 where netflix almost doubled its amount of shows on its platform.')

#Splitting Genres Column
netflix_df = netflix_df.assign(genres=netflix_df.genres.str.split(",")).explode('genres')
#Trim genres column
netflix_df["genres"] = netflix_df["genres"].apply(lambda x: x.strip())

#genres Dataframe showing the number of genres from 2018 and above
genres_df = netflix_df.groupby(['genres'])['genres'].count().reset_index(name='genres_count').sort_values('genres_count', ascending = False)

#genres_years_df showing the top 5 genres over the years from 2018 and above
genres_years_df = netflix_df.groupby(['release_year', 'genres', 'type'])['genres'].count().reset_index(name='genres_count').sort_values('genres_count', ascending = False)
genres_years_df = genres_years_df.query('release_year >= 2018')
genres_years_df = genres_years_df[(genres_years_df.genres.isin(list(genres_df['genres'][:5])))]

#Create 2 dataframes one for movies and one for series
movies = genres_years_df[genres_years_df['type']=='Movie']
TVShows = genres_years_df[genres_years_df['type']=='TV Show']


if chart_visual == 'Genres':
    
    st.subheader('What are the top genres released by year?')
    
    #Showing the differences between each type of ratings
    Conditions = st.radio('Pick your Show Type', ['Movies','TV Shows'])
    if Conditions == 'Movies':
        ## Sunburst showing the top 5 movies genres
        movie = px.sunburst(movies, path=['release_year', 'genres'], values='genres_count',
                      color='genres',
                      color_continuous_scale='RdBu')

        movie.update_layout(title="Top Genres of Movies Released by Year")
        st.plotly_chart(movie)
        st.caption("We can notice how from 2018 till 2021 the show genres is decreasing in amount from year to year. Shouldn't it be increasing? What's the problem? Maybe we should notify the directors, or do more research to find patterns about this problem.")
    elif Conditions == 'TV Shows':
        ## Sunburst showing the top 5 TVshows genres
        show = px.sunburst(TVShows, path=['release_year', 'genres'], values='genres_count',
                      color='genres',
                      color_continuous_scale='RdBu')

        show.update_layout(title="Top Genres of Series Released by Year")
        st.plotly_chart(show)
        st.caption("Over the years, there only is International TV Shows, which is a problem because there isn't much diversity to the customers. The organization should increase and the amount of genres for TV Shows.")

#yearly_added_shows_df dataframe showing the amount of shows added on Netflix every year
yearly_added_shows_df = netflix_df.groupby(['year_added', 'genres', 'type'])['type'].count().reset_index(name='show_count').sort_values(['year_added', 'show_count'], ascending = False)
#yearly_released_shows_df dataframe showing the amount of shows released worldwide every year
yearly_released_shows_df = netflix_df.groupby(['release_year', 'genres', 'type'])['type'].count().reset_index(name='show_count').sort_values(['release_year', 'show_count'], ascending = False)

yearly_released_shows_df = yearly_released_shows_df.query('release_year >= 2008')

if chart_visual == 'Shows over the years':
    st.subheader('Based on the top genres, is Netlfix adding more shows to their platform than it is released every year?')
    
    ## Set a Selectbox of the different genres
    all_genres = list(genres_years_df['genres'].unique())
    
    genres_multiselect_container = st.container()
    all_options = st.checkbox("Select all genres")
    selected_options = []
    if all_options:
        selected_options = all_genres
        
    genres_choices = genres_multiselect_container.multiselect(
        'Select the genres of shows you want over the years',
        all_genres,
        selected_options
    )
    
        
    filtered_added_df = yearly_added_shows_df[yearly_added_shows_df["genres"].isin(genres_choices)].groupby(["year_added", "type"], as_index=False)["show_count"].sum()
    filtered_released_df = yearly_released_shows_df[yearly_released_shows_df["genres"].isin(genres_choices)].groupby(["release_year", "type"], as_index=False)["show_count"].sum()
    
    ## Scatter PLot showing the comparaison of the shows added on Netflix vs. shows released by year
    shows_added_released = go.Figure()
    shows_added_released.add_trace(go.Scatter( 
        x=filtered_added_df.loc[filtered_added_df['type'] == 'Movie']['year_added'], 
        y=filtered_added_df.loc[filtered_added_df['type'] == 'Movie']['show_count'],
        mode='lines+markers',
        name='Movie: Year Added',
        marker_color='darkblue',
    ))
    shows_added_released.add_trace(go.Scatter( 
        x=filtered_added_df.loc[filtered_added_df['type'] == 'TV Show']['year_added'], 
        y=filtered_added_df.loc[filtered_added_df['type'] == 'TV Show']['show_count'],
        mode='lines+markers',
        name='TV Show: Year Added',
        marker_color='hotpink',
    ))


    shows_added_released.add_trace(go.Scatter( 
        x=filtered_released_df.loc[filtered_released_df['type'] == 'Movie']['release_year'], 
        y=filtered_released_df.loc[filtered_released_df['type'] == 'Movie']['show_count'],
        mode='lines+markers',
        name='Movie: Released Year',
        marker_color='royalblue',
    ))
    shows_added_released.add_trace(go.Scatter( 
        x=filtered_released_df.loc[filtered_released_df['type'] == 'TV Show']['release_year'], 
        y=filtered_released_df.loc[filtered_released_df['type'] == 'TV Show']['show_count'],
        mode='lines+markers',
        name='TV Show: Released Year',
        marker_color='pink',
    ))
    shows_added_released.update_xaxes(categoryorder='total descending')
    shows_added_released.update_layout( xaxis_title="Year", yaxis_title="Amount of Shows", title="Shows Added VS. Shows Released Every Year ")

    st.plotly_chart(shows_added_released)
    st.caption("We can notice that at first Netflix didn't add much shows compared to how many shows were released every year, however after 2017 we can see that Netflix added much more shows than the number of shows that were released every year.")