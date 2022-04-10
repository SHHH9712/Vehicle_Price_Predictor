from bs4 import BeautifulSoup
from py import process
import requests
import pandas as pd
from tqdm import tqdm
import multiprocessing
import os

print(f"data/url_list_{90011}.csv" in [f for f in os.listdir("data")])

car_url_list_name = f"data/url_list_{90011}.csv"
p = pd.read_csv(car_url_list_name)
for i in p.loc[:,"0"]:
    print(i)
    sleep(1)
    break
