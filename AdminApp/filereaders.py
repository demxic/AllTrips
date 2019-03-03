"""This module holds functions needed to read pbs.txt files and turn them into schedule classes"""
from AdminApp.adminregex import page_number_RE


def verify_files(data_folder: str, file_names: list) -> list:
    """
    Verify files existence in data_folder

    """
    files = list()
    for file_name in file_names:
        file_to_be_read = data_folder / file_name
        if file_to_be_read.is_file():
            print("file {} found".format(file_name))
            files.append(file_to_be_read)
        else:
            print("file {} not found!".format(file_name))
    return files


def page_number_remover(file: str) -> str:
    """
    Remove =======pagenumber======= string from trips.txt file

    When using PDF Mate converter tu turn each .pdf file into .txt, the app will insert
    such long string with page numbers. This must be removed in order to read all trips
    correctly

    """
    with open(file, 'r') as f:
        content = f.read()
        content_new = page_number_RE.sub(repl='', string=content)
    return content_new
