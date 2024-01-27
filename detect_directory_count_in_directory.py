import os
import sys

def get_directory_count_in(directory_absolute_path):
    try:
        entries = os.listdir(directory_absolute_path)
        count = 0

        for entry in entries:
            absolute_path = os.path.join(directory_absolute_path, entry)

            if os.path.isdir(absolute_path):
                count += 1

        return count

    except FileNotFoundError:
        print(f"디렉토리를 찾을 수 없습니다.: {directory_absolute_path}")
        sys.exit(1)

if __name__ == '__main__':
    arguments = sys.argv[1:]

    if len(arguments) != 1:
        raise ValueError("인자는 1개만 입력 가능합니다.")

    directory_path = arguments[0]

    print(get_directory_count_in(directory_path))
