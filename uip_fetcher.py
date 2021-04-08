import requests
import argparse
import datetime
import os
import sys
import json

#
# Atari uIP fetcher, a tool to recursively fetch files via Mariusz Buras' "uip-tools" and the 'Netusbee' Atari
# cartridge port dongle, in a structure that also enables booting the fetched files as a GEMDOS drive via an
# emulator such as Hatari (etc).
#
# By Jose Commins <axora@axora.net>
#
# Has been tested to mimic a 1:1 boot from a Megafile Atari drive with C, D, E, F partitions.
#
# Some current quirks to note:
# .TXT files get changed to .txt
# 0 byte length files error out - b0rks when attempting to get header length.
# Some files return huge sizes for some reason: E.g. 4294967295 bytes, which is a full unsigned 32-bit integer.
# Occasionally some unwholesome characters are returned - thus JSON read is forced to allow these to be present.
#


def fetch_directory_json_from_source(ip_address="", source_drive="", source_directory=""):
    url = "http://" + ip_address + "/" + source_drive[0] + source_directory.lstrip("/").rstrip("/") + "/?dir"
    print("URL: " + url)
    dir_result = requests.get(url, timeout=10)
    if dir_result.ok:
        return json.loads(dir_result.content, strict=False)
    return None


def recurse_fetch_directories_from_source(ip_address="", source_drive="", source_directory="",
                                          destination_directory="", max_recursion=4):
    file_identifier = "f"
    directory_identifier = "d"

    url = "http://" + ip_address + "/" + source_drive[0] + source_directory + "?dir"
    print("URL: " + url)
    fetch_result = requests.get(url, timeout=10)
    if fetch_result.ok:
        directory_json = json.loads(fetch_result.content, strict=False)
        for items in directory_json:
            item_name = items.get("name")
            item_type = items.get("type")
            # If directory, recurse if needed.
            if item_type == directory_identifier:
                save_directory_name = destination_directory.rstrip("/") + "/" + source_drive[0] + source_directory + item_name
                print("Creating dir: " + save_directory_name)
                if not os.path.exists(save_directory_name):
                    os.makedirs(save_directory_name)
                if max_recursion > 0:
                    print("Entering directory: " + item_name)
                    recurse_fetch_directories_from_source(ip_address=ip_address, source_drive=source_drive,
                                                          source_directory=source_directory + item_name + "/",
                                                          destination_directory=destination_directory,
                                                          max_recursion=max_recursion - 1)
            # If file, fetch - a bit more extended than regular requests to display progress.
            elif item_type == file_identifier:
                url = "http://" + ip_address + "/" + source_drive[0] + source_directory + item_name
                print("Fetching file: " + url)
                save_filename = destination_directory.rstrip("/") + "/" + source_drive[0] + source_directory + item_name
                with open(save_filename, "wb") as fp:
                    time_start = datetime.datetime.now()
                    try:
                        response = requests.get(url, stream=True, timeout=10)
                        total_length = response.headers.get("content-length")
                        if total_length is None:
                            print("File is zero length.")
                            fp.write(response.content)
                        else:
                            downloaded = 0
                            print("Size: " + total_length + " bytes.")
                            total_length = int(total_length)
                            for data in response.iter_content(chunk_size=4096):
                                downloaded += len(data)
                                fp.write(data)
                                done = int(50 * downloaded / total_length)
                                sys.stdout.write('\r[' + '=' * done + ' ' * (50 - done) + ']')
                                sys.stdout.flush()
                            time_end = datetime.datetime.now()
                            time_taken = time_end - time_start
                            print(" Done.  Rate: " + str(int(total_length / time_taken.total_seconds())) + " bytes/s.\n")
                    except requests.exceptions.RequestException as e:
                        print("**** ERROR - fetch failed: " + str(e) + "\n")
                        fp.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="uIP fetcher.")
    parser.add_argument("-ip", "--ip_address", type=str, help="IP address of Atari.", default="192.168.1.25")
    parser.add_argument("-a", "--atari_drive", type=str, help="Source drive letter on Atari.", default="C")
    parser.add_argument("-s", "--atari_directory", type=str, help="Source directory on Atari.", default="/")
    parser.add_argument("-d", "--destination_directory", type=str, help="Destination directory on host.", default="./My_Atari_Stuff")
    parser.add_argument("-r", "--max_recurse", type=int, help="Max directory recursion depth.", default=4)
    args = parser.parse_args()

    result = fetch_directory_json_from_source(ip_address=args.ip_address, source_drive=args.atari_drive, source_directory=args.atari_directory)
    if result is not None:
        print(result)

    recurse_fetch_directories_from_source(ip_address=args.ip_address, source_drive=args.atari_drive,
                                          source_directory=args.atari_directory, destination_directory=args.destination_directory,
                                          max_recursion=args.max_recurse)

    print("\n- Finished transferring files.")
