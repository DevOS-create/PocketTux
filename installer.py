import getpass
import os
import shutil
import sys
import zipfile

import requests

GITLAB_URL = "https://gitlab.com"
PROJECT_PATH = "DevOS/PocketTux"
BRANCH = "main"


def make_folder():
    folder = os.path.join(os.path.expanduser("~"), "PocketTux")
    if os.path.isdir(folder):
        print("Using existing folder:", folder)
    else:
        os.makedirs(folder)
        print("Created folder:", folder)
    return folder


def download_repo(token, folder):
    project = PROJECT_PATH.replace("/", "%2F")
    url = f"{GITLAB_URL}/api/v4/projects/{project}/repository/archive.zip"

    print("Downloading...")
    r = requests.get(
        url,
        headers={"PRIVATE-TOKEN": token},
        params={"sha": BRANCH},
        timeout=30,
    )

    if r.status_code == 401:
        print("Token rejected.")
        return None
    if r.status_code == 404:
        print("Project not found or no access.")
        return None
    r.raise_for_status()

    zip_path = os.path.join(folder, "repo.zip")
    with open(zip_path, "wb") as f:
        f.write(r.content)
    return zip_path


def unpack_zip(zip_path, folder):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if name.startswith("/") or ".." in name.split("/"):
                    print("Suspicious path in archive:", name)
                    return False
            zf.extractall(folder)
    except zipfile.BadZipFile:
        print("Downloaded file isn't a valid zip.")
        return False
    finally:
        os.remove(zip_path)

    entries = os.listdir(folder)
    if len(entries) == 1:
        inner = os.path.join(folder, entries[0])
        if os.path.isdir(inner):
            for item in os.listdir(inner):
                shutil.move(os.path.join(inner, item), os.path.join(folder, item))
            os.rmdir(inner)
    return True


def main():
    token = os.environ.get("GITLAB_TOKEN", "").strip()
    if not token:
        token = getpass.getpass("Access token: ").strip()
    if not token:
        print("Token is required.")
        return 1

    folder = make_folder()
    zip_path = download_repo(token, folder)
    if zip_path is None:
        return 1

    if not unpack_zip(zip_path, folder):
        return 1

    print("Done. Files are in:", folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
