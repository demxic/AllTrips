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
