import pandas as pd
import requests
import datetime
import spotipy
from  spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import base64
import os
from sqlalchemy.types import Integer,Text,DateTime

load_dotenv()

class Pandas_ETL():
    CLIENT_ID = os.environ.get('SP_CLIENT_ID')
    CLIENT_SEC = os.environ.get('SP_CLIENT_SECRET')

    # Data Getter
    def get_data(self):
        scope = 'user-library-read user-read-recently-played'

        today = datetime.datetime.now()
        past_90 = today - datetime.timedelta(days = 90)
        past_90_unix_timestamp = int(past_90.timestamp()) * 1000

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.CLIENT_ID,
        client_secret=self.CLIENT_SEC,
        redirect_uri='http://localhost:3000/callback',
        scope=scope))

        return sp.current_user_recently_played(limit=50)

    # Extract Method
    def extract(self):
        data = self.get_data()

        # Create lists to place values in Pandas Dataframe

        song_names = []
        artist_names = []
        played_at = []
        popularity = []

        for song in data['items']:
            song_names.append(song['track']['name'])
            artist_names.append(song['track']['album']['artists'][0]['name'])
            played_at.append(song['played_at'])
            popularity.append(song['track']['popularity'])

        song_dict = {
            "song_names": song_names,
            "artist_names": artist_names,
            "played_at": played_at,
            "popularity": popularity
        }

        song_df = pd.DataFrame(song_dict, columns=['song_names', 'artist_names', 'played_at', 'popularity'])

        print(song_df)

        return song_df

    def pop_check(self, pop_number):
        if pop_number > 50:
            return 'High'
        else:
            return 'Low'
    

    def transform(self):
        df = self.extract()

        # Check if our dataframe is empty
        if df.empty:
            print('No Songs Downloaded. Finishing Execution')
            return False

        # Primary Key Check
        if pd.Series(df['played_at']).is_unique:
            pass
        else:
            raise Exception(f'[Transform Error]: Primary Key Check not valid - Duplicated data in {df.columns.tolist()[2]} ')

        if df.isnull().values.any():
            raise Exception('No Real Values Found')

        # Adding Transformation Column 
        df['pop_range'] = df['popularity'].apply(self.pop_check)

        print(df)
        return df

        if self.transform():
            print('proceed to load')

        # LOAD
        print('...Loading...')

    def load(self):
        df = self.transform()
        connection = 'postgresql://postgres:YOUR-PW-HERE@127.0.0.1:5432/spotify_etl' #TODO Enter your PW here

        df.to_sql('recent_song_popularity', index=False, con = connection, if_exists='append',
        schema = 'public', chunksize = 500, dtype = {
            'song_names':Text,
            'artist_names':Text,
            'played_at':DateTime,
            'popularity':Integer,
            'pop_range':Text
        })

        return df

etl = Pandas_ETL()
# etl.load()
etl.transform()