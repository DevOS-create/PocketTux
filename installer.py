import os
import shutil
import zipfile

import requests

GITLAB_URL = "https://gitlab.com"
PROJECT_PATH = "DevOS/PocketTux"
BRANCH = "main"


def make_folder():
    home = os.path.expanduser("~")
    folder = os.path.join(home, "PocketTux")

    if not os.path.exists(folder):
        os.makedirs(folder)
        print("Created folder:", folder)
    else:
        print("Folder already exists:", folder)

    return folder


def download_repo(token, folder):
    encoded_path = PROJECT_PATH.replace("/", "%2F")
    url = f"{GITLAB_URL}/api/v4/projects/{encoded_path}/repository/archive.zip"
    headers = {"PRIVATE-TOKEN": token}
    params = {"sha": BRANCH}

    print("Downloading...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 401:
        print("Error: the token was not accepted.")
        return None
    if response.status_code == 404:
        print("Error: project not found. Check the project path and token access.")
        return None
    if response.status_code != 200:
        print("Error: download failed with status", response.status_code)
        return None

    zip_path = os.path.join(folder, "repo.zip")
    with open(zip_path, "wb") as file:
        file.write(response.content)

    return zip_path


def unpack_zip(zip_path, folder):
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(folder)

    os.remove(zip_path)

    entries = [name for name in os.listdir(folder) if name != "repo.zip"]
    if len(entries) == 1:
        inner_path = os.path.join(folder, entries[0])
        if os.path.isdir(inner_path):
            for item in os.listdir(inner_path):
                shutil.move(os.path.join(inner_path, item), os.path.join(folder, item))
            os.rmdir(inner_path)


def main():
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        token = input("Access token: ").strip()

    if token == "":
        print("A token is required.")
        return

    folder = make_folder()

    zip_path = download_repo(token, folder)
    if zip_path is None:
        return

    unpack_zip(zip_path, folder)
    print("Done! Files are in:", folder)


main()
