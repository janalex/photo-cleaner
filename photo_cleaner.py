import argparse
import os
import re
import stat

regex_pattern = r'(?P<name>\S+)\s*\(\d+\)\.(?P<ext>.+)'
regex_prog = re.compile(regex_pattern)


def log(msg: str):
    if options.verbose:
        print(msg)


class CachedInfo:
    def __init__(self, isfile: bool, size: int):
        self.isfile = isfile
        self.size = size


def process_dir(dirname: str) -> list[str]:
    to_remove = []
    cached_basefiles: dict[str, CachedInfo] = {}
    with os.scandir(dirname) as it:
        for entry in it:
            if entry.is_file():
                m = regex_prog.match(entry.name)
                if m:
                    base_name = f'{m.group('name')}.{m.group('ext')}'
                    full_name = os.path.join(dirname, base_name)
                    cached = cached_basefiles.get(full_name)
                    if cached:
                        if cached.isfile and cached.size == entry.stat().st_size:
                            to_remove.append(entry.path)
                    else:
                        if not os.path.exists(full_name):
                            # remember that it doesn't exist to avoid future system calls for this filename
                            info = CachedInfo(False, 0)
                        else:
                            stats = os.stat(full_name)
                            info = CachedInfo(stat.S_ISREG(stats.st_mode), stats.st_size)
                            if info.isfile and info.size == entry.stat().st_size:
                                to_remove.append(entry.path)
                        cached_basefiles[full_name] = info
            elif entry.is_dir() and options.recursive:
                log(f"Processing subdirectory {entry.path}")
                to_remove += process_dir(entry.path)

    return to_remove


def remove_files(names: list[str]):
    for fname in names:
        log(f"Removing file '{fname}'")
        os.remove(fname)


def main():
    global options
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--recursive', action='store_true', help='Process subdirectories recursively')
    parser.add_argument(
        '-x',
        '--execute',
        action='store_true',
        help='Perform file removal, otherwise just prints duplicate filenames')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('dirs', metavar='dir-path', nargs='+', help='Directory to process')
    options = parser.parse_args()
    for dir in options.dirs:
        log(f"Processing '{dir}'...")
        output = process_dir(dir)
        if options.execute:
            remove_files(output)
        else:
            print(f'duplicate files: {output}')


if __name__ == "__main__":
    main()
