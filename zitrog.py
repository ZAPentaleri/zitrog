#/usr/bin/python3

"""
A Q&D utility for re-encoding modern MP3 ID3 tags into obsolete encoding formats
for use with outdated devices -- MP3 players, PDAs, localized PC media players,
etc. At present, only Unicode decoding and Shift-JIS encoding are supported, but
other formats may be added in the future.
"""

import argparse

from enum import Enum
from os import makedirs as os_makedirs
from os import path as os_path
from os import remove as os_remove
from re import search as re_search
from re import sub as re_sub
from textwrap import wrap
from unidecode import unidecode

class Action(Enum):
    RETRO = 'retroencode'

# DEFAULT_PRESERVED_TAGS = ("TALB", "TPE1", "TPE2", "TCOP", "COMM", "TPOS", "TCON", "TIT2", "TRCK", "TYER",)
DEFAULT_PRESERVED_TAGS = ("TALB", "TPE1", "TPE2", "TCOP", "TPOS", "TCON", "TIT2", "TRCK", "TYER",)

ID3_DATA_FLAG_SIZE = 2

ID3_DELIMITER = b"\x00"

ENCODING_ISO       = "ISO-8859-1"
ENCODING_UNICODE   = "UTF-16"
ENCODING_SHIFT_JIS = "Shift-JIS"

LOGO = """
                              _______ ______     __
                              \___  // ||   \   / /
                                 / //  || |\ | / /
                                / // / || |/ |/ /
                               / //_/| ||  _//_/
                              /_____\|_||_| /_/ (R)

                           Zoe's ID3 Tag Retroencoder
                              for Outdated Devices
                                    (ZITROG)
"""

accepted_corrections = {}

def print_log_lines(tab_depth_or_line_one, *definite_lines):
    tab_content = "    "

    tab_depth_provided = type(tab_depth_or_line_one) == int
    tab_depth = tab_depth_or_line_one if tab_depth_provided else 0
    lines = [
        *([] if tab_depth_provided or tab_depth_or_line_one is None else [tab_depth_or_line_one]),
        *definite_lines,
    ]

    for line in lines:
        print(f"{tab_content * tab_depth}{line}")

def yes_no(prompt):
    while True:
        decision = input(f"{prompt} (y/n)> ").strip().lower()

        if decision == 'y':
            return True
        elif decision == 'n':
            return False

def padded_hex(input_int):
    hex_str = hex(input_int)[2:].upper()

    return f"0x{(len(hex_str) % 2) * '0'}{hex_str}"

def encode_data(data):
    return ID3_DELIMITER + data.encode(ENCODING_SHIFT_JIS) + ID3_DELIMITER

def validate_data_encode(data):
    try:
        encode_data(data)
        return True
    except:
        return False

def identify_encode_error_positions(data):
    error_positions = []

    for char_index,char in enumerate(data):
        try:
            char.encode(ENCODING_SHIFT_JIS)
        except UnicodeEncodeError:
            error_positions.append(char_index)
        except:
            print_log_lines(
                "===== FATAL ENCODING ERROR =====",
                f"RAW FRAME DATA: {data_raw}",
                f"DECODED FRAME DATA (from {'utf-16' if data_is_unicode else 'iso'}): {alt_data_decoded}",
                f"REFERENCE ENCODE (utf-8): {alt_data_decoded.encode()}",
            )

            raise initial_encoding_error

    return error_positions

def suggest_data_changes(data, error_positions):
    return "".join(
        char if char_index not in error_positions
        else decoded_char if (decoded_char:=unidecode(char)) != char else "_"
        for char_index,char in enumerate(data)
    )

def read_id3(input_path, preserved_tags=DEFAULT_PRESERVED_TAGS, automatic_correction=False, verbose=False):
    print_log_lines(
        "=====",
        f"INPUT PATH: {input_path}"
    )

    with open(input_path, "rb") as input_file:
        id3_definition = {
            "header": None,
            "frames": [],
            "content_offset": None,
        }

        id3_header = input_file.read(10)
        id3_identifier = id3_header[:3].decode(ENCODING_ISO)
        # id3_flags = id3_header[3:6]
        id3_size_encoded = id3_header[6:10]
        id3_size = int(
            "".join(
                "{:08b}".format(byte)[1:] for byte in id3_size_encoded
            ),
            2
        )

        print_log_lines(
            id3_header,
            f"REPORTED SIZE: {padded_hex(id3_size)}",
            # id3_identifier,
            "",
            "ID3 FRAMES:",
        )

        if id3_identifier != "ID3":
            raise "Invalid ID3 identifier"

        id3_definition["header"] = id3_header[:6]
        id3_definition["content_offset"] = len(id3_header) + id3_size

        while True:
            frame_offset = input_file.tell()
            frame_header = input_file.read(8)

            tag_name = frame_header[:4].decode(ENCODING_ISO)

            if not bool(re_search(r"^[A-Z0-9]{4}$", tag_name)):  # invalid tag name check
                print_log_lines(1, f"INVALID NEXT HEADER @ {padded_hex(frame_offset)}: {frame_header}")

                return id3_definition

            data_length = int.from_bytes(frame_header[4:8], "big")
            data_flags  = input_file.read(ID3_DATA_FLAG_SIZE)
            data_raw    = input_file.read(data_length)

            data_is_unicode = data_raw[:1] == b"\x01"

            if tag_name not in preserved_tags:
                print_log_lines(1, f"Skipped tag @ {padded_hex(frame_offset)} with header {frame_header}")
                continue

            try:
                if data_is_unicode:
                    data_decoded = data_raw[1:-2].decode(ENCODING_UNICODE)
                else:
                    data_decoded = data_raw[1:-1].decode(ENCODING_ISO)
            except UnicodeDecodeError:
                print_log_lines(
                    "",
                    f"===== FATAL DECODING ERROR =====",
                    f"RAW FRAME HEADER: {frame_header}",
                    f"RAW FRAME DATA FLAGS: {data_flags}",
                    f"RAW FRAME DATA: {data_raw}",
                    "",
                )

                raise

            print_log_lines(
                1,
                f"{tag_name} [len:{padded_hex(data_length)}:{data_length}; "
                f"flag:{padded_hex(int.from_bytes(data_flags, 'big'))}] "
                f"{f'=v= {data_raw} ' if verbose else ''}"
                f"=~= {data_decoded[0:255] if data_decoded is not None else None}",
            )

            if not data_is_unicode:
                data_encoded = data_raw
            else:
                try:
                    alt_data_decoded = accepted_corrections[data_decoded]
                except:
                    alt_data_decoded = data_decoded

                data_encoded = None
                while data_encoded is None:
                    if validate_data_encode(alt_data_decoded):
                        data_encoded = encode_data(alt_data_decoded)
                    else:
                        error_positions = identify_encode_error_positions(alt_data_decoded)
                        suggested_data_decoded = suggest_data_changes(alt_data_decoded, error_positions)

                        print_log_lines(
                            "",
                            f"!!! ENCODING ERROR ON <{tag_name}> @ POS.{','.join(str(x) for x in error_positions)} !!!",
                            "",
                            f"{'ACCEPT ' if not automatic_correction else ''}"
                            f"AUTOMATIC CORRECTION"
                            f"{'' if not automatic_correction else ' ACCEPTED'}"
                            f" \"{data_decoded}\" >>> \"{suggested_data_decoded}\""
                            f"{' ?' if not automatic_correction else ''}",
                            "",
                        )

                        manual_correction = (
                            input("Enter to Accept, or Submit Own Correction> ").strip() if not automatic_correction
                            else ""
                        )

                        if manual_correction == "":
                            data_encoded = encode_data(suggested_data_decoded)
                            accepted_corrections[data_decoded] = suggested_data_decoded
                        elif validate_data_encode(manual_correction):
                            data_encoded = encode_data(manual_correction)
                            accepted_corrections[data_decoded] = manual_correction
                        else:
                            alt_data_decoded = manual_correction

            id3_definition["frames"].append({
                "tag": tag_name,
                "data_flags": data_flags,
                "data": data_encoded,
                "data_was_converted": data_is_unicode,  # if data was unicode, it got converted
            })

            print_log_lines(
                2,
                f"{'>>> Re-encode as Shift-JIS' if data_is_unicode else 'Passthru as ISO'} >>> {data_encoded}"
            )

def write_id3(input_path, output_dir_path, id3_definition, auto_overwrite=False, ):
    original_file_name,original_file_extension = os_path.splitext(os_path.basename(input_path))

    new_file_name = original_file_name

    output_path = os_path.join(output_dir_path, f"{new_file_name}{original_file_extension}")

    print_log_lines(
        "",
        # f"{original_file_name}{original_file_extension} >>> {new_file_name}{original_file_extension}",
        f"OUTPUT PATH: {output_path}",
    )

    try:
        os_makedirs(output_dir_path, exist_ok=True)

        if not auto_overwrite and os_path.isfile(output_path) and not yes_no("File exists at output path. Allow overwrite?"):
            print_log_lines("", "File skipped.",)
            return

        os_remove(output_path)
    except OSError:
        pass

    assembled_frames = b""
    for frame_index,frame in enumerate(id3_definition["frames"]):
        assembled_frames += frame["tag"].encode(ENCODING_ISO)
        assembled_frames += len(frame["data"]).to_bytes(4, "big")
        assembled_frames += frame["data_flags"]
        assembled_frames += frame["data"]

    assembled_frames += ID3_DELIMITER * 32  # not sure why I'm doing this, but a buffer seems like a good idea

    with open(output_path, "wb") as output_file:
        output_file.write(id3_definition["header"])
        output_file.write(
            int(
                "".join(
                    f"0{byte}" for byte in wrap("{:028b}".format(len(assembled_frames)), 7)
                ),
                2,
            ).to_bytes(4, "big")
        )
        output_file.write(assembled_frames)

        with open(input_path, "rb") as input_file:
            input_file.seek(id3_definition["content_offset"])
            output_file.write(input_file.read())

    return

def main():
    arg_parser = argparse.ArgumentParser(
        "id3_retroencode",
        description=f"{LOGO}\n\n{__doc__}",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    arg_parser.add_argument(
        "-a", "--action", type=str,
        help=f"Tag processing action\nSupported actions: {Action.RETRO.value}",
    )
    arg_parser.add_argument("-i", "--input", type=str, nargs="+", help="Input file path (accepts multiple, wildcards)",)
    arg_parser.add_argument("-o", "--output", type=str, help="Output directory",)
    arg_parser.add_argument(
        "-p", "--preserve", type=str, nargs="+", default=DEFAULT_PRESERVED_TAGS,
        help=f"Tags to preserve. Tags which are not explicitly\n"
             f"preserved, or which do not occur in the input file, will\n"
             f"not be encoded in the output file.\n"
             f"Defaults to: {' '.join(DEFAULT_PRESERVED_TAGS)}",
    )
    arg_parser.add_argument(
        "-u", "--automatic", action="store_true",
        help="Automatically accept suggested tag changes for character\nrestrictions in output encoding",
    )
    arg_parser.add_argument(
        "-w", "--overwrite", action="store_true",
        help="Overwrite existing files on output without prompt",
    )
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output during encoding",)

    arguments = arg_parser.parse_args()

    print_log_lines(
        f"Action:          {arguments.action}",
        f"Input Paths:     {arguments.input}",
        f"Output Dir Path: {arguments.output}",
        f"Preserved Tags:  {arguments.preserve}",
    )

    if arguments.action.lower() == Action.RETRO.value:
        for input_path in arguments.input:
            id3_definition = read_id3(input_path, arguments.preserve, arguments.automatic, arguments.verbose,)
            write_id3(input_path, arguments.output, id3_definition, arguments.overwrite,)

if __name__=="__main__":
    main()
