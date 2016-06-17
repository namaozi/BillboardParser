# encoding:UTF-8
import re
import sys
import json

TRIAD = ["maj", "min", "dim", "aug"]
MODIFIER = ["b", "#"]

#popular-styleとの対応表
#タプルで持たせた方が後々よさそう？
#sus2, 5(パワーコード)を追加
#dim7とdimを区别する必要無し。
CHORD_TABLE = {"maj":("maj", ""), "min":("min", "m"), "dim":("dim","dim", "o"), "aug":("aug", "aug"), "maj7":("maj7", "M7", "△7"), "min7":("min7", "m7"), "7":("7", "7"), "dim7":("dim7", "dim", "o"), "hdim7":("hdim7", "m7b5"), "minmaj7":("minmaj7", "mM7"), "maj6":("maj6", "6"), "min6":("min6", "m6"), "9":("9", "9"), "maj9":("maj9", "M9"), "min9":("min9", "m9"), "sus4":("sus4", "sus4"), "sus2":("sus2", "add9"), "5":("5", "5")}

#シャープとフラットの対応表
SHARP_TO_FLAT = {"C#":"Db", "D#":"Eb", "F#":"Gb", "G#":"Ab", "A#":"Bb",
                "E#":"f", "B#":"C"}

def get_degree_from_pitch_number(pitch_number):
    mod = pitch_number % 12
    if mod == 0:
        return "I"
    elif mod == 1:
        return "IIb"
    elif mod == 2:
        return "II"
    elif mod == 3:
        return "IIIb"
    elif mod == 4:
        return "III"
    elif mod == 5:
        return "IV"
    elif mod == 6:
        return "Vb"
    elif mod == 7:
        return "V"
    elif mod == 8:
        return "VIb"
    elif mod == 9:
        return "VI"
    elif mod == 10:
        return "VIIb"
    elif mod == 11:
        return "VII"
    else:
        return "NONE"


def get_pitch_number(root):
    #脳筋
    if root == "C":
        return 0
    elif root == "C#" or root == "Db":
        return 1
    elif root == "D":
        return 2
    elif root == "D#" or root == "Eb":
        return 3
    elif root == "E":
        return 4
    elif root == "F":
        return 5
    elif root == "F#" or root == "Gb":
        return 6
    elif root == "G":
        return 7
    elif root == "G#" or root == "Ab":
        return 8
    elif root == "A":
        return 9
    elif root == "A#" or root == "Bb":
        return 10
    elif root == "B":
        return 11
    else:
        return -1

#shorthandを受け取り、triadに簡略化して返す
def make_triad_from_full(shorthand):
    #TRIADを含んでればそれで、他は消す.
    for tri in TRIAD:
        result = re.search(tri, shorthand)
        if result is not None: #あたり
            tmp = re.search(":", shorthand)
            return tri
        else: #ハズレ
            pass
    #該当しなければメジャーで
    #ほんとにｗ？
    return "maj"


def make_root_note(chord_full):
    # スラッシュがあればルート音変えねばならん
    result = re.match("/", chord_full)
    #スラッシュがなければNATURAL + MODIFIERだけ返す
    if result is None:
        # 正規表現使ってもいいけど、重そうなのでやめてる
        for mod in MODIFIER:
            if chord_full[1] == mod:
                return chord_full[:2]
        return chord_full[0]
    else: #onコード
        return chord_full[0]
