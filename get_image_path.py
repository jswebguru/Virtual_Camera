import logging
import os


def list_files_in_directory(directory, folders_only=False):
    file_paths = []  # This list will store all file paths
    if folders_only:

        # Iterate over items in the current directory
        for item in os.listdir(directory):
            # Create full path
            item_path = os.path.join(directory, item)
            # Check if the item is a directory (subfolder)
            if os.path.isdir(item_path):
                file_paths.append(item_path)
        if len(file_paths) == 0:
            file_paths.append(directory)
        return file_paths

    for root, _, all_files in os.walk(directory):
        for i, each in enumerate(all_files):
            file_path = os.path.join(root, each)
            file_paths.append(file_path)
            # if i > 10:
            #     return file_paths
    return file_paths


if __name__ == '__main__':
    logging.info(f'In the output folder, there are {list_files_in_directory("images")} images')
