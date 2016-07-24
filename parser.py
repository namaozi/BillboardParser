# encoding:UTF-8
import re
import sys
import math
import json

import functions as func

# ver.8(16/07/24) ナインスコードを4和音に省略
# ver.7 1つもコードが入っていないrepeatSegmentsを排除しました
# ver.6 chorusSegmentsを消してrepeatSegmentsに統合しました。(JSONs4)
###BPMを直すのが無理っぽいので諦めました。。。フラグ制御、可読性無さ過ぎ。

# ver.5 構造情報egmentsの取得(Aメロとか), x◯とかで繰り返しになるやつの判定をする。完全版、だと信じたい。
# ver.4 BPMの追加、popular-styleをもっとちゃんと作ったり。DUPLICATEDを排除したのがでかい。さらに全部シャープをフラットに統一したよ。みたびJSONの作成。(現行のJSONs2です)
# ver.3 クローリングして得たgenreをsongに入れたりとか。ふたたびJSONの作成。(JSONs2は死にました)
# ver.2の改良版.しょうがないからまたプレーンテキストからJSON作るよ.
# 作ったJSONはJSONs2へ.


NATURAL = ["A", "B", "C", "D", "E", "F", "G"]
SHORTHAND = ["maj", "min", "dim", "aug", "maj7", "min7", "7", "dim7", "hdim7", "minmaj7", "maj6", "min6", "9", "maj9", "min9", "sus4"]
#ナインスコードをセブンスコードに変更しました
CHORD_TABLE = {"maj":("maj", ""), "min":("min", "m"), "dim":("dim","dim", "o"), "aug":("aug", "aug"), "maj7":("maj7", "M7", "△7"), "min7":("min7", "m7"), "7":("7", "7"), "dim7":("dim7", "dim", "o"), "hdim7":("hdim7", "m7b5"), "minmaj7":("minmaj7", "mM7"), "maj6":("maj6", "6"), "min6":("min6", "m6"), "9":("9", "7"), "maj9":("maj9", "add9"), "min9":("min9", "m7"), "sus4":("sus4", "sus4"), "sus2":("sus2", "add9"), "5":("5", "5")}
SHARP_TO_FLAT = {"C#":"Db", "D#":"Eb", "F#":"Gb", "G#":"Ab", "A#":"Bb", "E#":"f", "B#":"C"}

# メイン関数
if __name__ == "__main__":

    #まずindex.csvを開く
    #index.csvからは、同期に必要なidとchart_dateを取得する。
    file_list = open( "./inputs/billboard-2.0-index_replaced.csv", 'r')
    file_genre = open("./inputs/result_genre.csv", "r")

    contents = file_list.read()
    file_list.close()
    #なんか知らないけどエクセルで開くと改行が"\r"に改変される
    lines_list = contents.split("\n")
    contents = file_genre.read()
    file_genre.close()
    lines_genre = contents.split("\n")

    #カウンタ
    count_song = 0

    # 楽曲情報たち
    title = ""
    artist = ""
    metre = ""
    tonic = "" #キー
    year = 0
    tonic_number = 0

    # ジャンルについて.
    dic_genre = {}

    # かぶり曲探知
    duplicate_check_dic = {}

    # その他
    count = 0
    filename = "salami_chords.txt"

    ### file_listの内容
    # 0:id	1:chart_date	2:target_rank	3:actual_rank	4:title     5:artist	6:peak_rank	7:weeks_on_chart
    # chart_dateは発売日ではないけど、まぁしょうがないでしょ…

    ### file_genreの内容
    # 0:id 1~:genre(複数)

    # 行数はsong_idとほぼ同義(1行目が0とかそういうの)
    # salami_chordsとresult.csv, genre.csv, writer.csvの行数を同期するために工夫せねば
    id_list = 0
    id_genre = 0
    # 0000 ~ 1301まで
    for song_id in range(1, 1301):

        ### 各ファイルの切り出し
        # indexは0始まりなので注意
        cells_list = lines_list[id_list].split(",")
        cells_genre = lines_genre[id_genre].split(",")
        id_list += 1
        id_genre += 1

        # まずidが一致しているのか調べる(一致させました...)
        while int(cells_list[0]) != song_id:
            print("LIST ERROR")
        while int(cells_genre[0]) != song_id:
            print("GENRE ID ERROR")

        # idしかなくて曲が登録されてなければ飛ばす
        # cellsの長さで判断
        if len(cells_genre) <= 1:
            continue

        #else:
        count_song += 1

        ###chart_dateからyearを得る
        chart_date = cells_list[1]
        year = int(chart_date.split("/")[0])

        #ジャンル,ライターを成形する
        #多少は直したけど表記ゆれの吸収とかやらねば
        #
        # 0:id, 1:title, 2:genre, 3:空白 とかなので長さ4以上であればジャンルを持つ
        if len(cells_genre) >= 4:
            # 0:id, 1:titleなのでそれ以降を取得.
            # cellsの最後が空の場合が多いので消しておこう
            if cells_genre[len(cells_genre) - 1] == "":
                cells_genre = cells_genre[:-1]

            for i, cell in enumerate(cells_genre[2:]):
                if cell == "" or cell == " ":
                    continue
                # 小文字化, 文字列の頭 or 末尾が空白なら消す.
                cell = cell.lower()
                cells_genre[2 + i] = cell

                if cell[0] == " ":
                    cell = cell[1:]
                if cell[len(cell)-1] == " ":
                    cell = cell[:-1]

                if cell not in dic_genre:
                    dic_genre[cell] = 1
                # あればインクリメント
                else:
                    dic_genre[cell]+= 1
            #print len(cells_genre), cells_genre[2:]



        ### billboard側
        # make four-digit string 0000 ~ 1301
        song_id_str = ""
        digit_length = int(math.log10(song_id) + 1)
        for tmp in range(4 - digit_length):
            song_id_str += str(0)
        song_id_str += str(song_id)

        #please set
        f = open( "./McGill-Billboard/" + song_id_str + '/' + filename, 'r')
        print("open", song_id_str)
        #DUPLICATEDの場合ファイルを作りたくないのであとでファイル作成します

        # JSON直下のdictionary, "song"とか"chords"とかはこれにブチ込む
        # rootにブチ込むdictionaryもここで宣言
        root_dic = {}
        song_dic = {}
        chord_array = [] #chordは配列
        container = {}

        # コード関係
        chord_index = 0

        #構造情報関連の変数
        struct_symbol = ""
        struct_name = ""
        struct_index_start = 0
        struct_index_end = 0
        struct_start_time = 0
        struct_length = 0
        struct_dic = {}
        repeat_segments = []

        #サビ関連の変数
        #BPM判定関連
        #切り分けがめんどいのでそのままやっていきます。。。
        chorus_flag = 0
        chorus_started = 0
        chorus_index_start = 0
        chorus_index_end = 0
        time_start = 0
        time_start_bar_length = 0
        time_start_next = 0
        time_get_flag = 0

        # とりあえず1行ごとに区切っておく
        contents = f.read()
        f.close()
        lines = contents.split("\n")
        # 1行ごとに見ていく...
        for line_id ,line in enumerate(lines):
            #print "line_id", line_id
            # 最初の4行,コロンと空白の後に楽曲情報が続く
            if line_id < 4:
                result = re.search(":", line)
                #endはマッチ終了位置を返す
                #endを使えば一つづつ切り出すことが可能

                if re.search("title", line):
                    title = line[result.end()+1:]
                elif re.search("artist", line):
                    artist = line[result.end()+1:]
                elif re.search("metre", line):
                    metre = line[result.end()+1:]
                elif re.search("tonic", line):
                    tonic = line[result.end()+1:]
                    tonic_number = func.get_pitch_number(tonic)
                else: #なにもしない
                    pass
                continue

            # それ以降の本体部分
            # まず空行をはじく
            if line == "":
                continue
            #途中でtonic や metreが変わることがある
            #とりあえずはtonicだけ変えておく…
            if line[0] == "#":
                if line[2] == "t": #トニックが変わるサインだ！
                    #print "TONIC CHANGE:", line
                    #ハードコーディング申し訳ない
                    tonic = line[9:]
                    tonic_number = func.get_pitch_number(tonic)
                    #print tonic, tonic_number
                continue

            #初期化する前にサビ1段目の小節数を！
            if time_get_flag == 1:
                time_start_bar_length = bar_index + 1
                #print "time_start_bar_length", time_start_bar_length

            # タブ前の時間情報を除外
            sentence = line.split("\t")[1] #これはコレクションでなく文字列
            #print sentence

            # 次の先頭には構造情報 or コメント or パイプが来る
            # 正規表現の場合はエスケープシーケンスに気をつけること
            result = re.match("\|", sentence)
            if result is not None: #行頭がパイプのとき
                pass

            # コメントもしくは構造情報が先頭にあるとき。
            # 小節情報をリセット
            else:
                bar_index = -1 #インクリメント位置の都合上-1に初期化
                result = re.search("\|", sentence) #パイプで区切る
                if result:
                    #これでsymbolとnameに切り分けられる
                    struct_info = sentence[:result.start()].split(", ")
                    #まずは2つめの要素=nameがあるか調べる
                    if struct_info[1] is not "":
                        #このとき、前のstructが終わりを告げるのでやっと前のlengthがわかる
                        #インクリメントしているので1つ前で終わっている
                        struct_index_end = chord_index - 1
                        if struct_index_end > 0: #0のときは1発目なので前のstructがない
                            #print "start, end:",struct_index_start, struct_index_end
                            struct_length = struct_index_end - struct_index_start

                            #struct_length < 0 は排除する.
                            if struct_length < 0:
                                continue
                            #1つ前のstructをやっとここで登録します
                            #!!!これより前でstructとかを使わない!!!

                            #同じシンボルでも全然違う時があるので、symbol + nameで調べた方がよい
                            symbol_plus_name = struct_symbol + struct_name
                            #そして、初出なのかを調べる
                            if symbol_plus_name not in struct_dic:
                                #初出であれば、まずdicをrepeat_segmentsに用意する
                                #この時点でわかる情報はid,startなので先に登録しておく
                                repeat_segments.append({"symbol":struct_symbol,"struct":struct_name,"repeats":[{"id":struct_index_start,"start":struct_start_time,"length":struct_length}]})
                                struct_dic[symbol_plus_name] = 1
                            else: #既にそのsymbol + nameがでているならば…
                                struct_dic[symbol_plus_name] += 1
                                #同じsymbol + nameを持つrepeatSegmentsのrepeats要素に辞書型でid,length,startを追加する.
                                for (iterate_i, each_dic) in enumerate(repeat_segments):
                                    #各イテレーションで、symbol と nameが同じなのか調べる
                                    each_symbol_plus_name = each_dic["symbol"] + each_dic["struct"]
                                    #こういうところisにすると🙅🙅🙅
                                    if each_symbol_plus_name == symbol_plus_name:
                                        repeat_segments[iterate_i]["repeats"].append({"id":struct_index_start,"start":struct_start_time,"length":struct_length})

                        #こちらは今見ているsymbolの解析
                        #終わったら登録するのがポイント
                        #これを次のstructまでとっておきます
                        struct_index_start = chord_index
                        struct_symbol = struct_info[0]
                        struct_name = struct_info[1]
                        #時間もとっておきましょう
                        struct_start_time = int(float(line.split("\t")[0]) * 1000)

                    #サビフラグ立てる
                    if re.search(" chorus", sentence):
                        chorus_flag = 1
                    else: #chorusじゃなければフラグ折る
                        chorus_flag = 0

                    # 行頭の構造情報とかを消しましょう
                    sentence = sentence[result.end()-1:]


            #ここまで行頭の構造情報に着目してました
            #しばらくコーラスの解析をします
            ################################
            # 解読不能なのでいずれ直したい #
            ################################
            # #コーラス開始の次の小節
            if time_get_flag == 1:
                time_start_next = float(line.split("\t")[0])
                #print "time_start_next", time_start_next
                time_get_flag = 2

            #サビ処理
            if chorus_flag != 0 :
                #サビ始まりを検知
                if chorus_started == 0:
                    #サビ開始の時間とを取得
                    if time_get_flag == 0:
                        time_start = float(line.split("\t")[0]) #これで時間情報を採れます
                        #print "time_start",time_start
                        time_get_flag = 1
                    #スタートindexを記憶
                    chorus_index_start = chord_index
                    chorus_started = 1
                    #print "chorus start :", chorus_index_start
                else:
                    pass
            #chorus_flagが折れているのにstartedが立っている場合
            #つまり初回以降のサビ。
            if chorus_flag == 0 and chorus_started > 0:
                chorus_index_end = chord_index - 1
                #print "chorus end :", chorus_index_end
                #フラグ折る
                chorus_started = 0

            #次に繰り返し構造を抽出します
            how_many_repeat = 0 #繰り返しの数、毎行ゼロに更新したいのでここ。
            local_repeat_array = [] # x◯みたいになっているコードをぶち込む。
            #エックスを含んでいると×2とかになるっぽい…？
            result = re.search(" x", sentence)
            if result:
                #print line
                #闇のコード… parseIntを実現します
                how_many_repeat = int(''.join([x for x in sentence[result.end():] if x.isdigit()]))

            #ここでいよいよコードの切り分け
            #sentenceには構造情報含まれていない
            #まずパイプで区切り、そのあと空白で区切る
            bar_contents = sentence.split("|")
            for bar_content in bar_contents:

                #小節中にコロンを含んでいればコード情報アリ？
                #よく分からん行末のコメントは飛ばしていいか…
                if re.search(":", bar_content) is None:
                    continue
                bar_index += 1 #小節インクリメント

                #次に空白で区切る
                elements = bar_content.split(" ")
                # 要素の1文字目がコードシンボルの音ならばコードである
                #print elements
                for name_full in elements:
                    #print "a",name_full,"a"
                    if name_full == "": #たまに空白が入る時があるので殺す.
                        continue

                    if name_full[0] in NATURAL:

                        #のちのちcsvに吐き出すのでカンマをセミコロンに置き換え
                        name_full = name_full.replace(",", ";")
                        #まずピッチと種類で分離しましょう
                        fragment = name_full.split(":")
                        note_absolute = fragment[0]
                        shorthand_full = fragment[1]
                        note_number = func.get_pitch_number(note_absolute)

                        #ここでシャープはフラットに変換します
                        if re.search("#", note_absolute):
                            note_absolute = SHARP_TO_FLAT[note_absolute]
                        #もし、FbとかCbとかいう表記があったら直してください
                        if re.search("Fb", note_absolute):
                            print(name_full)
                            note_absolute = "E"
                        if re.search("Cb", note_absolute):
                            print(name_full)
                            note_absolute = "B"


                        #とりあえずonコードは無視して、情報変換しましょう
                        shorthand_triad = func.make_triad_from_full(shorthand_full)
                        note_degree = func.get_degree_from_pitch_number(note_number - tonic_number)

                        #違う表記も用意します！！！！
                        #括弧とスラッシュを両方もっているやつもいるので、先に括弧から調べます
                        #括弧（）がある時、無視して（）以前を取得します
                        popular_style = note_absolute
                        result = re.search("\(", shorthand_full) #バックスラッシュ必要
                        if result is not None:
                            #これでスラッシュ以前がとれます
                            shorthand_full = shorthand_full[:result.end() - 1]

                        #オンコードは無視、スラッシュがあればスラッシュ以前で切り取る
                        else:
                            result = re.search("/", shorthand_full)
                            if result is not None:
                                shorthand_full = shorthand_full[:result.end() - 1]

                        #shorthand_fullがテーブルの表記にあるコードタイプならば、フルで登録
                        if shorthand_full in CHORD_TABLE:
                            popular_style += CHORD_TABLE[shorthand_full][1]
                        #それ以外の表記のとき
                        #諦めましょう、だいたいよく分からない表記の時です…triadで代替.
                        else:
                            popular_style += CHORD_TABLE[shorthand_triad][1]
                            #print "abnormal name :", name_full, popular_style

                        #代理変数
                        name_triad = note_absolute + ":" + shorthand_triad
                        name_full = note_absolute + ":" + shorthand_full
                        degree_full = note_degree + ":" + shorthand_full
                        degree_triad = note_degree + ":" + shorthand_triad

                        # chord_arrayにブチ込みます
                        chord_array.append({"index":chord_index, "bar":bar_index, "name-full":name_full, "name-triad":name_triad, "degree-full":degree_full, "degree-triad":degree_triad, "popular-style":popular_style})

                        #さらに、how_many_repeatが0でなければ、local_repeat_arrayにコードをブチ込む
                        if how_many_repeat > 0:
                            local_repeat_array.append({"index":chord_index, "bar":bar_index, "name-full":name_full, "name-triad":name_triad, "degree-full":degree_full, "degree-triad":degree_triad, "popular-style":popular_style})

                        chord_index += 1
                        #print name_full, name_triad, degree_full, degree_triad

            #各行の終わりにすること。
            #x◯がついてるやつをちゃんと再現します
            if how_many_repeat > 0:
                if local_repeat_array:
                    #x◯の分だけ余計にchord_arrayにappendします
                    for iterate_l in range(1, how_many_repeat):
                        local_bar_length = int(local_repeat_array[-1]["bar"]) - int(local_repeat_array[0]["bar"]) + 1
                        #めんどいのでめっちゃ略記してます
                        for c in local_repeat_array:
                            # print "index, bar:",chord_index, c["bar"] + local_bar_length * iterate_l, c["popular-style"]
                            # bar_lengthに注意.
                            chord_array.append({"index":chord_index, "bar":c["bar"] + local_bar_length, "name-full":c["name-full"], "name-triad":c["name-triad"], "degree-full":c["degree-full"], "degree-triad":c["degree-triad"], "popular-style":c["popular-style"]})
                            #実際にchord_indexを増やします.
                            chord_index += 1

                        #print iterate_l
                        #print local_repeat_array



        #1曲のファイルを見た後にすること
        # print json.dumps(repeat_segments, indent=4)

        #metre, 拍子の調査
        beat_devider = 0
        if metre == "4/4" or metre == "12/8":
            beat_devider = 4
        elif metre == "3/4":
            beat_devider = 3
        elif metre == "2/4" or metre == "6/8":
            beat_devider = 2
        elif metre == "5/4" or beat_devider == "5/8":
            beat_devider = 5
        elif metre == "7/4": #pink floyd
            beat_devider = 7
        else:
            print("\nabnormal\n")
            beat_devider = 4

        #コーラス1段目のbeat_timeを調べましょう
        #まずは1小節の長さ
        bar_time = 0
        if time_start_bar_length is not 0:
            bar_time = (float(time_start_next) - float(time_start)) / time_start_bar_length
        else: #コーラスが無い曲のBPMは適当に設定
            bar_time = 2.5 #適当に設定

        #これをmetreに従った拍数で割りましょう
        beat_time = bar_time / beat_devider
        bpm = int(60 / beat_time)
        #遅すぎるのは奇妙なので早くします
        if bpm < 50:
            bpm *= 2
        if bpm < 50: #それでもなお遅い場合
            bpm *= 2
        print ("BPM:", bpm)

        #楽曲情報をJSONの"song"に登録する
        #artistとtitleが同じ曲は、登録しません。
        artist_title = artist + title
        if artist_title in duplicate_check_dic:
            print(title, artist, "DUPLICATED!!!")
            duplicate_check_dic[artist_title] += 1
            continue
        else: #かぶりチェック辞書にartist, titleの対を登録
            #artistとtitleの連結で登録.......
            duplicate_check_dic[artist_title] = 1

        #DUPLICATEDじゃないなら、JSONファイルを作成する(書き込みは最後にまとめる)
        fj = open("./outputs/" + song_id_str + ".JSON", "w")

        song_dic["id"] = song_id
        song_dic["title"] = title
        song_dic["artist"] = artist
        song_dic["tonic"] = tonic
        song_dic["metre"] = metre
        song_dic["year"] = year
        #beatとBPMを追加します
        song_dic["beat"] = beat_devider
        song_dic["bpm"] = bpm
        #cells_genreは序盤で成形したので3以上です
        if len(cells_genre) >= 3:
            song_dic["genre"] = cells_genre[2:]
        else:
            song_dic["genre"] = []

        root_dic["song"] = song_dic

        #繰り返し情報を"repeatSegments"に登録
        root_dic["repeatSegments"] = repeat_segments

        #コード情報を"chords"に登録
        root_dic["chords"] = chord_array

        #print json.dumps(root_dic, indent=4)

        # ファイルに書き込みは最後にまとめて！
        json.dump(root_dic, fj)

    # 結果発表
    print("count_song :", count_song)
