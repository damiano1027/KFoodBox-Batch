# KFoodBox-Batch
KFoodBox 프로젝트의 배치 스크립트 레포지토리

### 파일
`foods.csv`
  - 최초 서비스에서 제공할 음식 리스트

`insert_foods_to_mysql.py`
  - 한식진흥원 또는 LampCook에서 제공하는 음식 소개 정보를 크롤링하여 mysql DB에 저장
    
`insert_recipes_to_mysql.py`
  - 한식진흥원에서 제공하는 특정 음식의 레시피 정보를 크롤링하여 mysql DB에 저장
  - 재료 정보는 제외
