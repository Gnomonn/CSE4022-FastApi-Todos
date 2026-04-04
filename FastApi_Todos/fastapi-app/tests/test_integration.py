import requests

def test_production_api_alive():
    # 배포된 실제 주소
    url = "http://163.239.77.78:8011/todos"
    response = requests.get(url)
    
    # 200 OK가 나오는지 자동으로 확인
    assert response.status_code == 200
    # 본인 데이터가 들어있는지 확인
    assert "20221543" in response.text