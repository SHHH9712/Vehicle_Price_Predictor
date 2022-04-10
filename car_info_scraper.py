from bs4 import BeautifulSoup
from py import process
import requests
import pandas as pd
from tqdm import tqdm
import multiprocessing
import os

def get_url_list(zip_code, radius, pages = 50):
    """
    This function will return a list of urls that links to car pages on cars.com
    Inputs:
        zip_code: target area zip code
        radius: searhc radius in miles
        pages: number of page to scrap, total number of car urls will be pages
    """
    url_list = []
    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    }

    for page in range(1,pages+1):
        page = str(page)
        radius = str(radius)
        zip_code = str(zip_code)
        url_base = 'https://www.cars.com/shopping/results/?dealer_id=&keyword=&list_price_max=&list_price_min=&makes[]=&maximum_distance={}&mileage_max=&page={}&page_size=100&sort=best_match_desc&stock_type=used&year_max=&year_min=&zip={}'.format(radius, page, zip_code)
        
        response = requests.get(url_base, headers=header)
        data = response.text
        soup = BeautifulSoup(data, "html.parser")
        
        for segment in soup.find_all(class_="vehicle-card-link js-gallery-click-link"):
            url_list.append("https://www.cars.com"+segment.get('href'))

    return url_list

all_basics = set()

def get_car_info(url):
    """
    This function uses a url to cars.com page and retrieve informations from it and return a dict contains all those informaiton, 
    which includes:  car_name,price,Exterior_color,Interior_color,Drivetrain, 
                     MPG_low,MPG_high,Fuel_type,Transmission,Engine,Mileage,
                     rating,Comfort_rating,Interior_design_rating,Performance_rating,
                     Value_rating,Exterior_styling_rating,Reliability_rating,features,
                     zip_code
    Inputs: 
        url links to car page on cars.com
    """
    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    }
    response = requests.get(url, headers=header)
    data = response.text
    soup = BeautifulSoup(data, "html.parser")

    price = soup.find(class_="primary-price").string
    price = filter(str.isdigit, price)
    price = int("".join(price))

    car_name = soup.find(class_ = "listing-title").string.strip()

    Exterior_color = -1
    Interior_color  = -1
    Drivetrain  = -1
    MPG_low = -1
    MPG_high = -1
    Fuel_type = -1 
    Transmission = -1
    Engine = -1
    Mileage = -1

    description = soup.find_all(class_ = "fancy-description-list")
    for name, value in zip(description[0].find_all('dt'), description[0].find_all('dd')):
        name = name.string.strip()
        value = value
        all_basics.add(name)
        if name == "Exterior color":
            Exterior_color = value.string.strip()
        elif name ==  "Interior color":
            Interior_color = value.string.strip()
        elif name ==  "Drivetrain":
            Drivetrain = value.string.strip()
        elif name ==  "MPG":
            if(len(value.find_all("span")) != 0):
                MPG = value.find_all("span")[-1].string
                MPG_low, MPG_high = int(MPG.split('–')[0]), int(MPG.split('–')[1])
        elif name ==  "Fuel type":
            Fuel_type = value.string.strip()
        elif name ==  "Transmission":
            Transmission = value.string.strip()
        elif name ==  "Engine":
            Engine = value.string.strip()
        elif name ==  "Mileage":
            Mileage = filter(str.isdigit, value.string)
            Mileage = int("".join(Mileage))

    features = []
    features_raw = soup.find_all(class_ = 'all-features-item')
    for f in features_raw:
        features.append(f.string)
    features = '###'.join(features)

    rating = soup.find(class_ = "sds-rating__count").string
    rating_breakdown = soup.find(class_="review-breakdown").find_all(class_ = "sds-definition-list__value")
    Comfort_rating = rating_breakdown[0].string
    Interior_design_rating = rating_breakdown[1].string
    Performance_rating = rating_breakdown[2].string
    Value_rating = rating_breakdown[3].string
    Exterior_styling_rating = rating_breakdown[4].string
    Reliability_rating = rating_breakdown[5].string
    

    return {
        "car_name":car_name, 
        "price":price, 
        "Exterior_color":Exterior_color, 
        "Interior_color":Interior_color, 
        "Drivetrain":Drivetrain, 
        "MPG_low":MPG_low, 
        "MPG_high":MPG_high, 
        "Fuel_type":Fuel_type, 
        "Transmission":Transmission, 
        "Engine":Engine, 
        "Mileage":Mileage,
        "rating":rating,
        "Comfort_rating":Comfort_rating,
        "Interior_design_rating":Interior_design_rating,
        "Performance_rating":Performance_rating,
        "Value_rating":Value_rating,
        "Exterior_styling_rating":Exterior_styling_rating,
        "Reliability_rating":Reliability_rating,
        "features":features
            }

def scrap_all_car_from_region(zip_code):
    """
    This function takes a zip_code and scrap some number of cars information ans store it in csv
    """
    

    #get all the url for cars listing pages and save in csv
    print(f"{zip_code} starting.....")
    car_url_list = get_url_list(zip_code, radius = 50, pages = 50)
    car_url_list_name = f"data/url_list_{zip_code}.csv"
    pd.DataFrame(car_url_list).to_csv(car_url_list_name, index = False)

    #get cars information using the urls generated above
    print("{zip_code} working on cars.....")
    count = 0
    car_feature_csv = -1
    for car_url in tqdm(car_url_list):
        try:
            car_info = get_car_info(car_url)
            car_info["zip_code"] = str(zip_code)
            car_info = pd.DataFrame(car_info, index=[count])
            if(type(car_feature_csv) != int):
                car_feature_csv = pd.concat([car_feature_csv, car_info])
            else:
                car_feature_csv = car_info
            count += 1
        except:
            err_count += 1
            print(car_url) 
    car_feature_csv.to_csv(f"data/cars_{zip_code}.csv")
     

if __name__ == "__main__":
    #All the major city's zipcode in US
    zip_code_csv = pd.read_csv("major_city_zip_code.csv", on_bad_lines='skip')
    zip_code_list = zip_code_csv["zip_code"]

    #uses multiprocessing to accelerate
    process_list = []
    for zip_code in zip_code_list:
        p =  multiprocessing.Process(target= scrap_all_car_from_region, args = [zip_code])
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()


    
