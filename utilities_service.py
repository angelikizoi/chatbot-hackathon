import os
import requests


def download_image(url):
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        raise Exception("Failed to fetch image")

    # From content-disposition header find the filename
    content_disposition = response.headers.get("content-disposition")
    if content_disposition and "filename=" in content_disposition:
        file_name = content_disposition.split("filename=")[1].replace('"', "")
    else:
        file_name = url.split("/")[-1]  # If header does not exist, take name from the url

    # Create directory
    dir_path = os.path.join(os.getcwd(), "files")
    os.makedirs(dir_path, exist_ok=True)

    # Save the image
    file_path = os.path.join(dir_path, file_name)
    with open(file_path, "wb") as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)

    return file_path

def remove_image(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
