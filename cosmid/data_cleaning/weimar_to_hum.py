import re
import os
import sqlite3
import pandas as pd

from ..constants import PROJECT_ROOT, humdrumR

def fmt_key(key: str) -> str:
    if key == "":
        return key
    if len(key.split("-")) == 2:
        root, tonality = key.split("-")
    else:
        root = key
        tonality = "major"
    root = root.replace("b", "-")
    if tonality in ["min", "dor"]:
        root = root.lower()
    return f"*{root}:"

def get_melids(cur: sqlite3.Cursor) -> list[str]:
    cur.execute("SELECT DISTINCT melid FROM melody_type;")
    result = cur.fetchall()
    return [melid for melid, in result]

def extract_data_from_db_to_df(cur: sqlite3.Cursor, melid: str) -> pd.DataFrame:
    data = pd.DataFrame({"timestamp": [], "chord": [], "bar": [], "beat": []})
    cur.execute("SELECT onset, bar, beat, chord FROM beats WHERE melid = ? ORDER BY onset ASC;", (melid,))
    result = cur.fetchall()
    for onset, bar, beat, chord in result:
        new_row = pd.DataFrame({"timestamp": [onset], "chord": [chord], "bar": [bar], "beat": [beat]})
        data = pd.concat([data, new_row], ignore_index=True)
    data = data.assign(new_measure = (data["bar"] != data["bar"].shift()))
    return data

def get_solo_info(cur: sqlite3.Cursor, melid: str) -> tuple[str, str, str, str]:
    cur.execute("SELECT performer, title, key, signature FROM solo_info WHERE melid = ?", (melid,))
    performer, title, key, signature = cur.fetchone()
    return performer, title, key, signature

def add_spine_info(spines: dict[str, list[str]], key: str, signature: str) -> dict[str, list[str]]:
    # key sig *k[]
    # key *E:
    # meter M4/4
    for interpretation in spines:
        spine_info = ["*k[]", fmt_key(key), f"*M{signature}"]
        spines[interpretation].extend(spine_info)
    return spines

def add_records(spines: dict[str, list[str]], melid_data: pd.DataFrame) -> dict[str, list[str]]:
    for _, row in melid_data.iterrows():
        # add measure lines
        if row["new_measure"]: # type: ignore
            for interpretation in spines:
                spines[interpretation].append(f"={int(row['bar'])}")
        # add records
        spines["timestamp"].append(str(row["timestamp"]))
        spines["weimar"].append(str(row["chord"]) if row["chord"] not in ["", None] else ".")
        spines["harte"].append(weimar_chord_to_harte(str(row["chord"])))
    # close spines
    for interpretation in spines:
        spines[interpretation].extend(["==", "*-"])
    return spines

def find_root_note(chord: str) -> str:
    note_names = []
    for note_letter in ["A","B","C","D","E","F","G"]:
        note_names.extend([note_letter, note_letter + "#", note_letter + "b"])
    note_names_found = []
    for note_name in note_names:
        if note_name in chord[:min(3,len(chord))]:
            note_names_found.append(note_name)
    if len(note_names_found) == 0:
        raise Exception("not parseable: " + chord)
    if len(note_names_found) == 1:
        root_note = note_names_found[0]
    else:
        # G and G# - choose the longer string
        root_note = max(note_names_found, key = lambda note_name: len(note_name))
    return root_note

def weimar_chord_to_harte(chord: str) -> str:
    if chord in ["", None, "NC"]:
        return "."

    harte_chord = substitute_weimar_chord_syntax(chord)
    root_note = find_root_note(harte_chord)

    if "/" in harte_chord:
        chord_split = harte_chord.split("/")
        chord_split[0] = construct_harte_chord(harte_chord, root_note)
        harte_chord = "/".join(chord_split)
    else:
        harte_chord = construct_harte_chord(harte_chord, root_note)
            
    try:
        harte_chord = humdrumR.harte(harte_chord)[0]
    except Exception as e:
        print(chord, harte_chord)
        raise Exception(e)
    return harte_chord

def construct_harte_chord(harte_chord: str, root_note: str) -> str:
    extens = []
    chord_type = ""
    if ("maj" not in harte_chord and "min" not in harte_chord and "7" in harte_chord):
        extens = split_by_specific_integers(harte_chord.split(root_note)[1])
    elif "dim" in harte_chord:
        chord_type = "dim"
        extens = harte_chord.split(root_note + "dim")  
    elif "aug" in harte_chord:
        chord_type = "aug"
        extens = harte_chord.split(root_note + "aug")
    elif "maj7" in harte_chord or "maj6" in harte_chord:
        chord_type = "maj"
        extens = harte_chord.split(root_note + "maj")
    elif "min7" in harte_chord or "min6" in harte_chord:
        chord_type = "min"
        extens = harte_chord.split(root_note + "min")
    elif "minmaj7" in harte_chord:
        chord_type = "minmaj"
        extens = harte_chord.split(root_note + "minmaj")
    if "" in extens:
        extens.remove("")
    if len(extens) > 1:
        if extens[0] == "7":
            extens = ["1", "3", "5"] + extens
        harte_chord = root_note.replace("b", "-") + ":" + chord_type + "(" + ",".join(extens) + ")"
    elif len(extens) == 1:
        harte_chord = root_note.replace("b", "-") + ":" + chord_type + ",".join(extens)
    return harte_chord

def substitute_weimar_chord_syntax(chord: str) -> str:
    chord = chord.replace("j", "maj")
    if "-6" in chord:
        chord = chord.replace("-6", "min6")
    elif "6" in chord:
        chord = chord.replace("6", "maj6")
    chord = chord.replace("-", "min").replace("sus", "").replace("m7b5", "hdim7").replace("o", "dim").replace("+", "aug")
    # extensions
    chord = chord.replace("9b", "b9").replace("9#", "#9").replace("11b", "b11").replace("11#", "#11").replace("13b", "b13").replace("13#", "#13")
    return chord

def split_by_specific_integers(s: str):
    """
    Splits a string so that characters attach to the integer that follows.
    Allowed integers: 7, 9, 11, 13.

    Example:
    >>> split_by_specific_integers("7b9b13")
    ['7', 'b9', 'b13']
    >>> split_by_specific_integers("7913")
    ['7', '9', '13']
    """
    pattern = r'(7|9|11|13)'
    tokens = re.split(pattern, s)
    
    result = []
    buffer = ""
    for token in tokens:
        if not token:
            continue
        if token in {"7", "9", "11", "13"}:
            # finish any buffer before the number
            if buffer:
                result.append(buffer + token)
                buffer = ""
            else:
                result.append(token)
        else:
            # store characters until we meet a number
            buffer = token
    return result 

def convert_spines_data_to_filelines(spines: dict[str, list[str]]) -> list[str]:
    filelines = []
    assert len(spines["timestamp"]) == len(spines["weimar"])
    num_records = len(spines["timestamp"])
    # interpretation headers
    filelines.append(
        "\t".join([
            "**" + x for x in list(spines.keys())
        ])
    )
    # records
    for idx in range(num_records):
        filelines.append(
            "\t".join([ 
                spines[interpretation][idx] for interpretation in spines
            ])
        )
    return filelines

def write_filelines_to_file(filelines: list[str], melid: str, title: str, performer: str, output_dir: str) -> None:
    filename = "_".join([str(melid), title, performer]) + ".hum"
    output_filepath = os.path.join(output_dir, filename)
    with open(output_filepath, "w") as f:
        f.writelines([line + "\n" for line in filelines])
    return

def main():
    weimar_db_path = os.path.join(PROJECT_ROOT, "data_raw", "weimar", "wjazzd.db")
    output_dir = os.path.join(PROJECT_ROOT, "data_clean", "weimar")
    with sqlite3.connect(weimar_db_path) as conn:
        cur = conn.cursor()
        melids = get_melids(cur)
        for melid in melids:
            print(melid)
            melid_data = extract_data_from_db_to_df(cur, melid)
            performer, title, key, signature = get_solo_info(cur, melid)
            spines = { "timestamp": [], "weimar": [], "harte": [] }
            spines = add_spine_info(spines, key, signature)
            spines = add_records(spines, melid_data) 
            filelines = convert_spines_data_to_filelines(spines)
            write_filelines_to_file(filelines, melid, title, performer, output_dir)
        cur.close()
    return
