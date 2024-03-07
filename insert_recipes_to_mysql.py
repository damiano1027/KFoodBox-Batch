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

class RecipeSequenceEntity:
    def __init__(self, food_id, sequence_number, content):
        self.food_id = int(food_id)
        self.sequence_number = int(sequence_number)
        self.content = content

    def __str__(self):
        return f"(food_id: {self.food_id}, sequence_number: {self.sequence_number}, content: {self.content}"

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

    recipe_sequence_entities = []

    with open(config_file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    db = mysql.connector.connect(
        host=yaml_data['db']['mysql']['host'],
        user=yaml_data['db']['mysql']['user'],
        password=yaml_data['db']['mysql']['password'],
        database=yaml_data['db']['mysql']['database']
    )

    cursor = db.cursor()

    print("크롤링 시작")
    for food in foods:
        if food.recipe_url == '직접입력':
            continue

        response = requests.get(food.recipe_url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        print(f"{food.name} 데이터 조회")

        sql = "SELECT * FROM `kfoodbox`.`food` WHERE `name` = %s"
        cursor.execute(sql, (food.name,))
        result = cursor.fetchone()
        if result is None:
            continue

        food_id = result[0]

        sequence_number = 1
        if food.recipe_url.startswith('https://www.hansik.or.kr'):
            contentResponses = soup.find_all('ol', class_='list-unstyled list-preparation mb-5')
            for contentResponse in contentResponses:
                for content in contentResponse.find_all('li'):
                    recipe_sequence_entities.append(RecipeSequenceEntity(food_id, sequence_number, content.text))
                    sequence_number += 1

    cursor.close()
    db.close()

    try:
        db = mysql.connector.connect(
            host=yaml_data['db']['mysql']['host'],
            user=yaml_data['db']['mysql']['user'],
            password=yaml_data['db']['mysql']['password'],
            database=yaml_data['db']['mysql']['database']
        )

        cursor = db.cursor()

        print("DB 삽입 시작")
        for entity in recipe_sequence_entities:
            sql = "INSERT INTO `kfoodbox`.`recipe_sequence` (`food_id`, `sequence_number`, `content`) VALUES (%s, %s, %s)"
            val = (entity.food_id, entity.sequence_number, entity.content)

            cursor.execute(sql, val)
            print(f"{entity.food_id}번 번호 음식의 {entity.sequence_number}번째 순서 내용 삽입중")

        db.commit()
        cursor.close()
        db.close()
        print("삽입 완료")
    except mysql.connector.Error as err:
        print("MySQL 에러 발생: ", err)
