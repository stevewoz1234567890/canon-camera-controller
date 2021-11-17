import requests
import json
import os

uri = "https://54.193.209.15:23118/"


def get_cookies(uri):
    key = os.getenv("FLASK_SECRET_KEY")
    login_url = f"{uri}/login_admin?key={key}"
    res = requests.get(login_url, verify=False)
    cookies = {'session': res.cookies['session']}
    return cookies


def check_user(uri, cookies):
    get_user = " { user { username } }"
    mutation = get_user
    variables = {}
    url = f'{uri}/graphql-api?query={mutation}&variables={json.dumps(variables)}'
    res = requests.post(url, verify=False, cookies=cookies)
    data = json.loads(res.text)
    print('checking who is logged in... user query returns', data)


def get_image():
    # grab image from internet for upload test
    r = requests.get("https://purplemana-media.s3.amazonaws.com/12/243532/zz__AP-122720-1-front-deskew.jpg",
                     stream=True)
    path = './test_image.jpg'
    if r.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    return path


def upload(uri, file_path, cookies, real_item_id=563, labels='testing'):
    # craft file upload request
    upload_url = f"{uri}/upload?labels={labels}&real_item_id={str(real_item_id)}"
    print("uploading to", upload_url)
    files = {'file': open(file_path, 'rb')}
    # do upload
    res = requests.post(upload_url, verify=False, cookies=cookies, files=files)
    print("response from file upload:", res.text)


if __name__ == '__main__':
    cookies = get_cookies(uri)
    check_user(uri, cookies)
    file_path = get_image()
    upload(uri, file_path, cookies)
