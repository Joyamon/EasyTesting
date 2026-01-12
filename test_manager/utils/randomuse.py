"""随机生成个人信息"""

import requests


def mock_user_info():
    url = 'https://randomuser.me/api/'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
    }
    form_type = {
        'dataType': 'json'
    }
    response = requests.get(url, data=form_type, headers=headers)
    return response.json()


if __name__ == '__main__':
    print(mock_user_info())
