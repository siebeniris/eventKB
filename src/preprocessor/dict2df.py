import json
import os

import pandas as pd
from pandarallel import pandarallel

from src.utils.utils import timing

pandarallel.initialize()


def get_long(geo):
    if str(geo) != 'nan':
        if 'coordinates' in geo:
            return geo['coordinates']['coordinates'][0]
        else:
            return None
    else:
        return None


def get_lat(geo):
    if str(geo) != 'nan':
        if 'coordinates' in geo:
            return geo['coordinates']['coordinates'][1]
        else:
            return None
    else:
        return None


def get_place_id(geo):
    if str(geo) != 'nan':
        if 'place_id' in geo:

            return geo['place_id']
        else:
            return None
    else:
        return None


def get_hashtags(entities):
    if str(entities) != 'nan':
        if 'hashtags' in entities:
            return [x['tag'] for x in entities['hashtags']]
        else:
            return None
    else:
        return None


def get_mentions(entities):
    if str(entities) != 'nan':
        if 'mentions' in entities:
            return [x['username'] for x in entities['mentions']]
        else:
            return None
    else:
        return None


def get_retweet(public_metrics):
    return public_metrics['retweet_count']


def get_like(public_metrics):
    return public_metrics['like_count']


def get_reply(public_metrics):
    return public_metrics['reply_count']


def get_quote(public_metrics):
    return public_metrics['quote_count']

##########################################

@timing
def dic2df(tweet_dict):
    tweets = tweet_dict['data']
    places = tweet_dict['places']
    # get geo information
    place_df = pd.DataFrame.from_dict(places, orient='index')
    place_df.rename(columns={'id': 'place_id'}, inplace=True)
    # tweets data df
    df = pd.DataFrame.from_dict(tweets, orient='index')

    # coordinates
    df['long'] = df['geo'].parallel_apply(get_long)
    df['lat'] = df['geo'].parallel_apply(get_lat)

    # prepare to use place_df
    df['place_id'] = df['geo'].parallel_apply(get_place_id)

    # hashtags, user mentions
    df['hashtags'] = df['entities'].parallel_apply(get_hashtags)
    df['user_mentions'] = df['entities'].parallel_apply(get_mentions)

    # user interactions
    df['reply_count'] = df['public_metrics'].parallel_apply(get_reply)
    df['like_count'] = df['public_metrics'].parallel_apply(get_like)
    df['retweet_count'] = df['public_metrics'].parallel_apply(get_retweet)
    df['quote_count'] = df['public_metrics'].parallel_apply(get_quote)

    # merge df and place_df
    merged = pd.merge(df, place_df, left_on='place_id', right_on='place_id', how='left')
    merged.rename(columns={'geo_y': 'geo'}, inplace=True)
    columns_reserved = ['author_id', 'conversation_id', 'text',
                        'id', 'created_at', 'lang',
                        'long', 'lat',
                        'hashtags', 'user_mentions',
                        'reply_count', 'like_count', 'quote_count',
                        'retweet_count',
                        'full_name', 'name', 'country', 'geo',
                        'country_code']
    merged = merged[columns_reserved]
    # merged['country_code'] = [country_code for x in range(len(merged))]
    return merged


@timing
def dict2df_one_file(input_file, outfile):
    with open(input_file) as reader:
        tweet_dict = json.load(reader)
    df_ls = []
    for country_code, tweet_dict in tweet_dict.items():
        df_country = dic2df(tweet_dict, country_code)
        print(country_code, len(df_country))
        df_ls.append(df_country)

    df = pd.concat(df_ls)
    df.index = df.id
    print(len(df))
    df.to_csv(outfile)


if __name__ == '__main__':
    # countries: ['GB', 'DE', 'SE', 'FR', 'IT', 'GR', 'ES', 'AT', 'HU', 'CH', 'PL', 'NL']
    # langs: ['en', 'fi', 'fr', 'de', 'el', 'nl', 'hu', 'ga', 'it', 'pl', 'es', 'sv']
    input_dir = 'data/output/preprocessed/restructured'
    out_dir = 'data/output/preprocessed/dataframes/'

    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            idx = filename.replace('.json', '')
            infile_path = os.path.join(input_dir, filename)
            with open(infile_path) as f:
                data = json.load(f)

            if len(data["conflict"]['data']) > 0:
                df_ = dic2df(data["conflict"])
                save_file_path = os.path.join(out_dir, f"{idx}.csv")
                df_.to_csv(save_file_path)
