import os
import json
from itertools import chain
from glob import glob
from collections import defaultdict

from src.utils.reader import read_gz_file, load_config
from src.utils.utils import timing


def extract_tweets_from_one_file_by_lang(filepath, language):
    """
    Extract tweets from one file
    :param filepath:
    :param language:
    :return:
    """
    data = read_gz_file(filepath)
    tweets = []
    for tweet in data['data']:
        lang = tweet['lang']
        if lang == language:
            tweets.append(tweet)
    new_data = {
        'data': tweets,
        'meta': data['meta'],
        'includes': data['includes']
    }
    return new_data


def extract_data_from_raw_data(data_dir, lang):
    data_dict = defaultdict(dict)

    count = 0
    for file in glob(data_dir + '/**/**.gz', recursive=True):
        print(file)
        filename = os.path.basename(file)
        country = filename.split('_')[0]
        if country not in data_dict:
            data_dict[country] = {
                'data': list(),
                'includes': {'places': list(), 'media': list()}
            }

        new_data = extract_tweets_from_one_file_by_lang(file, language=lang)
        if len(new_data['data']) > 0:
            # print(filename)

            data_dict[country]['data'].append(new_data['data'])
            if 'places' in new_data['includes']:
                data_dict[country]['includes']['places'].append(new_data['includes']['places'])
            if 'media' in new_data['includes']:
                data_dict[country]['includes']['media'].append(new_data['includes']['media'])
            count += len(new_data['data'])
    return data_dict, count


@timing
def get_tweet_dict_and_stats(data_dict):
    tweet_dict = defaultdict(dict)
    stats_dict = {}
    for country_code, d in data_dict.items():
        # print(country_code)

        data = list(chain.from_iterable(d['data']))
        tweet_d = {t['id']: t for t in data}

        places = list(chain.from_iterable(d['includes']['places']))
        places_d = {t['id']: t for t in places}
        media = list(chain.from_iterable(d['includes']['media']))
        media_d = {t['media_key']: t for t in media}

        stats_dict[country_code] = len(tweet_d)

        tweet_dict[country_code] = {
            'data': tweet_d,
            'places': places_d,
            'media': media_d
        }
    return stats_dict, tweet_dict


@timing
def restructure_crawled_tweets(data_dir, output_dir, idx, lang):
    # get data per country
    data_dict, count = extract_data_from_raw_data(data_dir=data_dir, lang=lang)
    print(f'the sum of tweets extracted: {count}')
    # get statistics of the data_dict.
    stats_dict, tweet_dict = get_tweet_dict_and_stats(data_dict)
    print(f"stats of tweets by countries {stats_dict}")
    with open(os.path.join(output_dir, f'{idx}.json'), 'w') as file:
        json.dump(tweet_dict, file)


def restructure_batch_data(output_dir, by_lang):
    for idx in [0, 1, 2, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16]:
        crawled_data_path = f"data/output/crawled/{idx}"
        restructure_crawled_tweets(crawled_data_path, output_dir, idx, by_lang)


if __name__ == '__main__':
    restructured_data_path = "data/output/preprocessed/restructured/"
    restructure_batch_data(restructured_data_path, by_lang="en")
