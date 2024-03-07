import requests
from bs4 import BeautifulSoup
import csv
import mysql.connector
import yaml

class Food:
    def __init__(self, category_id, origin_id, label_id, name, explanation_url, recipe_url):
        self.category_id = int(category_id)
        self.origin_id = int(origin_id)
        self.label_id = int(label_id)
        self.name = name
        self.explanation_url = explanation_url
        self.recipe_url = recipe_url

    def __str__(self):
        return f"(category_id: {self.category_id}, origin_id: {self.origin_id}, label_id: {self.label_id}, name: {self.name}, explanation_url: {self.explanation_url}, recipe_url: {self.recipe_url})"

class FoodEntity:
    def __init__(self, food_category_id, name, english_name, label_id, explanation, english_explanation, explanation_source, recipe_source):
        self.food_category_id = int(food_category_id)
        self.name = name
        self.english_name = english_name
        self.label_id = int(label_id)
        self.explanation = explanation
        self.english_explanation = english_explanation
        self.explanation_source = explanation_source
        self.recipe_source = recipe_source

    def __str__(self):
        return f"(food_category_id: {self.food_category_id}, name: {self.name}, label_id: {self.label_id}, explanation: {self.explanation}, explanation_source: {self.explanation_source}, recipe_source: {self.recipe_source})"

config_file_path = 'config.yaml'

if __name__ == '__main__':
    foods = []

    with open('foods.csv', 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)

        for row in csv_reader:
            category_id = int(row[0])
            origin_id = int(row[1])
            label_id = int(row[2])
            name = row[3]
            explanation_url = row[4]
            recipe_url = row[5]
            foods.append(Food(category_id, origin_id, label_id, name, explanation_url, recipe_url))

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
    }

    food_entities = []

    print("크롤링 시작")
    for food in foods:
        if food.explanation_url == '직접입력':
            continue

        response = requests.get(food.explanation_url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        name = None
        english_name = None
        explanation = None
        english_explanation = None
        explanation_source = None
        recipe_source = None

        if food.explanation_url.startswith('https://www.hansik.or.kr'):
            #name = soup.find('h2').text
            english_name = soup.find_all('span', class_='font-weight-normal')[1].text
            explanations = soup.find_all('td', style="white-space: normal;")
            explanation = explanations[0].text
            english_explanation = explanations[1].text
            explanation_source = '한식진흥원'
        elif food.explanation_url.startswith('http://lampcook.com'):
            #name = soup.find('h1', class_='h1_title').text.strip()
            english_name = soup.find_all('div', class_='def_color_box')[2].text.strip()
            explanations = soup.find_all('div', class_='txt_padd_box20 txt_ac')
            explanation = explanations[0].find('p').text
            english_explanation = explanations[1].find('p').text
            explanation_source = 'LampCook'

        if food.recipe_url.startswith('https://www.hansik.or.kr'):
            recipe_source = '한식진흥원'

        print(f"{food.name} 데이터 조회")

        food_entity = FoodEntity(food.category_id, food.name, english_name, food.label_id, explanation, english_explanation, explanation_source, recipe_source)
        food_entities.append(food_entity)

    with open(config_file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    try:
        db = mysql.connector.connect(
            host=yaml_data['db']['mysql']['host'],
            user=yaml_data['db']['mysql']['user'],
            password=yaml_data['db']['mysql']['password'],
            database=yaml_data['db']['mysql']['database']
        )

        cursor = db.cursor()

        print("DB 삽입 시작")
        for entity in food_entities:
            sql = None
            val = None

            if entity.explanation_source is None and entity.recipe_source is None:
                sql = "INSERT INTO `kfoodbox`.`food` (`food_category_id`, `name`, `english_name`, `label_id`, `explanation`, `english_explanation`) VALUES (%s, %s, %s, %s, %s, %s)"
                val = (entity.food_category_id, entity.name, entity.english_name, entity.label_id, entity.explanation, entity.english_explanation)
            elif entity.explanation_source is None:
                sql = "INSERT INTO `kfoodbox`.`food` (`food_category_id`, `name`, `english_name`, `label_id`, `explanation`, `english_explanation`, `recipe_source`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val = (entity.food_category_id, entity.name, entity.english_name, entity.label_id, entity.explanation, entity.english_explanation, entity.recipe_source)
            elif entity.recipe_source is None:
                sql = "INSERT INTO `kfoodbox`.`food` (`food_category_id`, `name`, `english_name`, `label_id`, `explanation`, `english_explanation`, `explanation_source`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val = (entity.food_category_id, entity.name, entity.english_name, entity.label_id, entity.explanation, entity.english_explanation, entity.explanation_source)
            else:
                sql = "INSERT INTO `kfoodbox`.`food` (`food_category_id`, `name`, `english_name`, `label_id`, `explanation`, `english_explanation`, `explanation_source`, `recipe_source`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                val = (entity.food_category_id, entity.name, entity.english_name, entity.label_id, entity.explanation, entity.english_explanation, entity.explanation_source, entity.recipe_source)

            cursor.execute(sql, val)
            print(f"{entity.name} 삽입중")

        db.commit()
        print("삽입 완료")
    except mysql.connector.Error as err:
        print("MySQL 에러 발생: ", err)
