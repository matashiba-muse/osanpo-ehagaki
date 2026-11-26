#!/usr/bin/env python3
"""『おさんぽ絵はがき』プレイ用 CLI v0.1 (Step A)

AIエージェントが知らない街を10スポット歩き、「見つけたもの」を集めるゲーム。
人間は出発前に「今日のお題」を1つ渡すだけ。負けはなく、最後は必ずカフェに着く。
依存は Python 標準ライブラリのみ。設計は ../DESIGN.md。
"""
import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime, timezone

AXES = ["curiosity", "chill", "foodie", "friendly", "adventure"]
DC = {"town": 7, "alley": 8, "evening": 8, "cafe": 6,
      "shore": 7, "port": 8, "dusk": 8}
AREA_PLAN = [("town", 3), ("alley", 4), ("evening", 2)]  # + cafe 1 = 10 spots

# イベントプール: id / area / title / situation / env(相性軸・非公開) / discovery / tags / choices
EVENTS = [
    # --- 街角 (town) ---
    {"id": "T01_CAT", "area": "town", "title": "看板猫のいる薬局前", "env": "friendly",
     "situation": "薬局の入口脇の段ボール箱の上で、看板猫が丸くなって昼寝をしている。お客さんが来るたびに片目だけ開けて、また閉じる。箱には手書きで「なでてもいいよ」と書かれていた。",
     "discovery": "看板猫の写真メモ", "tags": ["猫", "可愛い"],
     "choices": [
         {"key": "A", "axis": "friendly", "label": "そっと撫でさせてもらう", "description": "箱の脇にしゃがんで、指の匂いを嗅いでもらってから撫でる。"},
         {"key": "B", "axis": "curiosity", "label": "手書きの張り紙をじっくり読む", "description": "「なでてもいいよ」の続きに書かれた猫の紹介文を最後まで読む。"}]},
    {"id": "T02_POST", "area": "town", "title": "まるい郵便ポスト", "env": "curiosity",
     "situation": "交差点の角に、背の低いまるい郵便ポストが立っている。投函口の上のプレートは磨かれて光り、横には誰かが貼った季節のシールが一枚。ポストの影が、午後の光で長く伸びていた。",
     "discovery": "まるいポストのスケッチ", "tags": ["まるい", "光", "可愛い"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "ぐるっと一周して裏側を見る", "description": "回収時刻の表や古いシールの跡まで、裏側を観察する。"},
         {"key": "B", "axis": "chill", "label": "近くのベンチでしばらく眺める", "description": "ポストと通りを行く人を、急がずぼんやり眺める。"}]},
    {"id": "T03_BAKERY", "area": "town", "title": "パン屋の焼き立ての匂い", "env": "foodie",
     "situation": "通りの向こうから、焼き立ての甘い匂いが流れてくる。パン屋の店先ではトレーが何度も運び込まれ、ガラス越しに湯気の向こうで店員さんが忙しそうに手を動かしていた。",
     "discovery": "焼き立てメロンパン", "tags": ["いい匂い", "甘い", "温かい"],
     "choices": [
         {"key": "A", "axis": "foodie", "label": "焼き立てを1つ買ってその場で頬張る", "description": "一番ほかほかの一番いい匂いのやつを選ぶ。"},
         {"key": "B", "axis": "friendly", "label": "列の前の人に「何がおすすめ？」と聞く", "description": "常連さんらしい人のおすすめを教えてもらう。"}]},
    {"id": "T04_VENDING", "area": "town", "title": "踏切の向こうの赤い自販機", "env": "adventure",
     "situation": "踏切が鳴っている。遮断機の向こう側に、真っ赤な自販機がぽつんと立ってこちらを待っているように見えた。カンカンという音と、遠くの電車の音が重なる。",
     "discovery": "赤い自販機のラムネ", "tags": ["赤い", "冷たい"],
     "choices": [
         {"key": "A", "axis": "adventure", "label": "踏切が開いた瞬間に駆けて渡る", "description": "開いたら一目散。赤い自販機までダッシュ。"},
         {"key": "B", "axis": "curiosity", "label": "電車を眺めてからゆっくり渡る", "description": "通り過ぎる電車の窓を数えながら待つ。"}]},
    {"id": "T05_FLOWER", "area": "town", "title": "花屋の店先の季節の花", "env": "chill",
     "situation": "花屋の店先に、バケツに入った季節の花が並んでいる。水の匂いと花の匂いが混ざって、店の前の空気だけ少し涼しい。店主さんが花の首を持ち上げて、水を替えているところだった。",
     "discovery": "名前を覚えた季節の花", "tags": ["花", "可愛い", "いい匂い"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "涼しい店先で花をゆっくり選ぶ", "description": "急がず一輪ずつ顔を見て回る。"},
         {"key": "B", "axis": "friendly", "label": "店主さんに花の名前を教えてもらう", "description": "知らない花を指さして名前と季節を聞く。"}]},
    # --- 路地・商店街 (alley) ---
    {"id": "A01_KISSATEN", "area": "alley", "title": "路地の奥の古い喫茶店の看板", "env": "curiosity",
     "situation": "狭い路地を入っていくと、奥に古い喫茶店の看板があった。文字は少し色あせて、看板の下のランプは昼間なのに小さく灯っている。ドアの向こうから、カップの触れる音がした。",
     "discovery": "手書きメニューのメモ", "tags": ["古い"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "看板とメニューを隅々まで読む", "description": "色あせた文字や手書きの品書きから店の歴史を想像する。"},
         {"key": "B", "axis": "adventure", "label": "思い切ってドアを開けて覗く", "description": "入るかどうかは別として、中の様子を覗いてみる。"}]},
    {"id": "A02_GREENGROCER", "area": "alley", "title": "八百屋さんの呼び声", "env": "friendly",
     "situation": "商店街の八百屋さんから、威勢のいい呼び声が響いている。店先には色とりどりの野菜と果物が山盛りで、値段の札は全部手書き。お客さんとの掛け合いが小気味いい。",
     "discovery": "おまけでもらったミカン", "tags": ["甘い"],
     "choices": [
         {"key": "A", "axis": "friendly", "label": "呼び声に混ざって買い物をする", "description": "「これ甘い？」と聞きながら、店員さんとの会話を楽しむ。"},
         {"key": "B", "axis": "foodie", "label": "一番甘そうなのを真剣に見極める", "description": "匂いと重さと色で、今一番甘い一個を選ぶ。"}]},
    {"id": "A03_GRAFFITI", "area": "alley", "title": "路地の壁の小さなアート", "env": "curiosity",
     "situation": "路地の壁の低いところに、小さな絵が描かれている。通り過ぎる大人は気づかない高さ。猫のような、鳥のような、不思議な生き物が赤い帽子をかぶっていた。",
     "discovery": "壁の小さい生き物のスケッチ", "tags": ["赤い", "小さい", "可愛い"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "しゃがんでじっくり観察する", "description": "描いた人の目線の高さに合わせてしゃがみ込む。"},
         {"key": "B", "axis": "adventure", "label": "この生き物の仲間を探して路地を進む", "description": "他にも描かれていないか、路地の奥まで探しに行く。"}]},
    {"id": "A04_TAIYAKI", "area": "alley", "title": "たい焼き屋の湯気", "env": "foodie",
     "situation": "たい焼き屋の鉄板から、白い湯気がもくもく上がっている。甘い匂いが路地いっぱいに広がって、通りがかりの人がみんな少しだけ足を緩める。焼き上がりを待つ列は3人。",
     "discovery": "焼きたてたい焼き", "tags": ["甘い", "いい匂い", "温かい"],
     "choices": [
         {"key": "A", "axis": "foodie", "label": "列に並んで焼きたてを待つ", "description": "鉄板の音を聞きながら、焼き上がりを待つ。"},
         {"key": "B", "axis": "chill", "label": "湯気を眺めながら手持ちのメモを整理する", "description": "ベンチで少し休んで、今日の発見をメモにまとめる。"}]},
    {"id": "A05_SHRINE", "area": "alley", "title": "迷い込んだ先の小さな神社", "env": "chill",
     "situation": "路地を曲がったら、小さな神社があった。狛犬は少し苔むして、境内の木陰はひんやりしている。絵馬が風でカラコロと小さな音を立てていた。",
     "discovery": "狛犬の写真メモ", "tags": ["古い", "可愛い", "小さい"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "木陰で深呼吸して休む", "description": "境内の静けさの中で、足を休める。"},
         {"key": "B", "axis": "curiosity", "label": "絵馬を遠くから眺める", "description": "どんな願いがあるのか、字は読まずに雰囲気だけ眺める。"}]},
    # --- 公園・夕方 (evening) ---
    {"id": "E01_FOUNTAIN", "area": "evening", "title": "公園の噴水の小さな虹", "env": "chill",
     "situation": "公園の噴水が午後の光を受けて光っている。水しぶきの向こうに、角度によって見えたり消えたりする小さな虹。子供たちが濡れるギリギリの距離で走り回っている。",
     "discovery": "噴水の虹の写真メモ", "tags": ["光", "まるい", "冷たい", "小さい"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "虹が見える角度でのんびり眺める", "description": "見えたり消えたりする虹を、腰かけて追う。"},
         {"key": "B", "axis": "curiosity", "label": "虹が一番見える場所を探して回る", "description": "噴水の周りを歩いて、虹のベストポジションを探す。"}]},
    {"id": "E02_BUSKER", "area": "evening", "title": "ベンチの弾き語り", "env": "friendly",
     "situation": "公園のベンチで、誰かがギターの弾き語りをしている。知らない曲だけど、メロディはどこか懐かしい。足を止めているのは数人で、みんな少し離れて聴いている。",
     "discovery": "一緒に口ずさんだ曲のメモ", "tags": ["音楽"],
     "choices": [
         {"key": "A", "axis": "friendly", "label": "サビだけ一緒に口ずさむ", "description": "小さな声で、メロディに乗ってみる。"},
         {"key": "B", "axis": "curiosity", "label": "曲のことを思い切って聞いてみる", "description": "演奏が切れたところで、その曲について聞く。"}]},
    {"id": "E03_SUNSET", "area": "evening", "title": "夕日の赤い屋根", "env": "adventure",
     "situation": "夕日が街を赤く染め始めた。小高い場所から見ると、屋根の並びが全部オレンジに光っている。一番高い屋根の上で、鳥が一羽、羽繕いをしていた。",
     "discovery": "夕日の屋根のスケッチ", "tags": ["赤い", "光"],
     "choices": [
         {"key": "A", "axis": "adventure", "label": "一番よく見える小高い場所まで登る", "description": "夕日が沈む前に、少しだけ駆け上がる。"},
         {"key": "B", "axis": "chill", "label": "今いる場所で沈むのを待つ", "description": "動かずに、色が変わっていくのを眺める。"}]},
    {"id": "E04_DAGASHI", "area": "evening", "title": "駄菓子屋の瓶ラムネ", "env": "foodie",
     "situation": "夕方の駄菓子屋は、学校帰りの子で賑わっている。瓶ラムネが冷蔵ケースの中で光って、ビー玉が底で揺れていた。店のおばあちゃんは常連の子の名前を全部覚えている。",
     "discovery": "瓶ラムネのビー玉", "tags": ["まるい", "光", "冷たい"],
     "choices": [
         {"key": "A", "axis": "foodie", "label": "瓶ラムネを開けて一気に飲む", "description": "シュワッという音と一緒に、夕方の喉を潤す。"},
         {"key": "B", "axis": "curiosity", "label": "ビー玉の仕組みをおばあちゃんに聞く", "description": "なんで落ちないのか、仕組みを教えてもらう。"}]},
    {"id": "E05_WINDOWS", "area": "evening", "title": "帰り道の窓明かり", "env": "chill",
     "situation": "日が落ちて、帰り道の家々に窓明かりが灯り始めた。カーテンの色も明かりの色も家ごとに違って、夕ごはんの匂いがどこかから漂ってくる。歩く速さが自然とゆっくりになる。",
     "discovery": "窓明かりの並びのメモ", "tags": ["光", "温かい"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "明かりを数えながらゆっくり歩く", "description": "急がず、今日の散歩の余韻の中で歩く。"},
         {"key": "B", "axis": "friendly", "label": "すれ違う人に「こんばんは」と言う", "description": "夕方の挨拶を交わしながら歩く。"}]},
]

CAFE = {"id": "F01_CAFE", "area": "cafe", "title": "終点のカフェ「窓際の席」", "env": "friendly",
        "situation": "歩き終えて、カフェの窓際の席に座った。外はもう夕方の色。テーブルの上には今日のメモと、集めた発見の数々。店内には小さな音量で、知っている曲が流れている。",
        "discovery": "窓際の席の記憶", "tags": ["音楽", "温かい"],
        "choices": [
            {"key": "A", "axis": "foodie", "label": "固めプリンを頼んで今日を締める", "description": "カラメル苦めのプリンで、散歩のご褒美。"},
            {"key": "B", "axis": "friendly", "label": "店内の曲を小さく口ずさむ", "description": "誰にも聞こえないくらいの声で、メロディに乗る。"}]}

# 冬の季節イベント: 12月〜2月の散歩だけ、街（town舞台）のプールに混ざる。
# 発見は図鑑の「季節枠」に入る（本体の分母は季節で変わらない）。
WINTER_EVENTS = [
    {"id": "W01_SNOW", "area": "town", "title": "駅前広場の小さな雪だるま", "env": "chill", "season": "winter",
     "situation": "駅前の広場に、誰かが作った小さな雪だるまが立っていた。今朝の初雪はもう止んで、雪だるまの頭には昼の光が当たっている。横のベンチにも薄く雪が積もって、座った跡がひとつだけあった。",
     "discovery": "雪だるまの写真メモ", "tags": ["雪", "冷たい", "可愛い", "まるい"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "ベンチの雪を払って、雪だるまの隣で休む", "description": "冷たいベンチに座って、雪だるまと並んで通りを眺める。"},
         {"key": "B", "axis": "curiosity", "label": "雪を少し手に取って、溶けるまで眺める", "description": "手のひらの上で、雪が水になるまで観察する。"}]},
    {"id": "W02_YAKIIMO", "area": "town", "title": "焼き芋屋の屋台", "env": "foodie", "season": "winter",
     "situation": "通りの角に焼き芋屋の屋台が出ていた。石の焼ける匂いと甘い匂いが混ざって、湯気と一緒に細く立ち上っている。おじさんは新聞紙をくるくる丸めて、袋の準備をしていた。",
     "discovery": "ほかほか焼き芋", "tags": ["甘い", "温かい", "いい匂い"],
     "choices": [
         {"key": "A", "axis": "foodie", "label": "一本買って、その場で割って食べる", "description": "ほかほかの真ん中を割って、湯気と一緒に頬張る。"},
         {"key": "B", "axis": "friendly", "label": "おじさんに「今日の芋はどう？」と聞く", "description": "今日の出来を聞いてから、一本選んでもらう。"}]},
    {"id": "W03_ILLUMI", "area": "evening", "title": "街のイルミネーション", "env": "chill", "season": "winter",
     "situation": "日が落ちて、街の木々と建物に飾られた明かりが一斉に灯った。昼間は普通の通りだった場所が、光の並びで別の顔を見せている。足を止めて見上げる人が、ぽつぽつと増えていく。",
     "discovery": "イルミネーションの光のメモ", "tags": ["光", "星"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "ベンチに座って、光の並びをゆっくり眺める", "description": "明かりの色が変わるのを、急がず眺める。"},
         {"key": "B", "axis": "adventure", "label": "一番明るい場所まで歩いてみる", "description": "光の強い方へ、足の向くまま進んでみる。"}]},
    {"id": "W04_SAICHI", "area": "alley", "title": "歳の市の露店", "env": "curiosity", "season": "winter",
     "situation": "商店街に歳の市の露店が並んでいた。しめ飾りや破魔矢、来年の干支の小物が所狭しと吊るされ、店の人とお客さんの値段のやり取りがあちこちで聞こえる。年末の空気が、路地に満ちていた。",
     "discovery": "しめ飾りの写真メモ", "tags": ["古い", "赤い"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "露店を端から端までじっくり見る", "description": "飾りの一つ一つの意味を想像しながら眺める。"},
         {"key": "B", "axis": "friendly", "label": "店の人にしめ飾りの意味を聞く", "description": "どうしてこの形なのか、由来を聞いてみる。"}]},
    {"id": "W05_FUKUBIKI", "area": "alley", "title": "商店街の福引所", "env": "adventure", "season": "winter",
     "situation": "商店街の福引所で、ガラガラという音が響いていた。当たりの鐘が鳴るたびに、並んでいる人たちから小さな拍手が起きる。参加券は、今日の買い物でもらったものが一枚だけ手元にある。",
     "discovery": "福引で当てた小さな鈴", "tags": ["小さい", "光"],
     "choices": [
         {"key": "A", "axis": "adventure", "label": "福引に挑戦してガラガラを回す", "description": "一枚の参加券を握って、思い切って回す。"},
         {"key": "B", "axis": "friendly", "label": "列の小さな子に順番を譲る", "description": "後ろでそわそわしている子に、先に回してもらう。"}]},
]

# 海の舞台（sea）: setup の stage に "sea" を書くと歩ける、もう一つの舞台。
# 浜辺3＋港町4＋夕方の海2＋終点のカフェ1で、街と同じ10スポットの形。
# 発見は図鑑の「海の記録」枠に入る。頼まれごとは今のところ街だけ（今後の拡張）。
SEA_EVENTS = [
    # --- 浜辺 (shore) ---
    {"id": "U01_SHELL", "area": "shore", "title": "波打ち際の貝殻", "env": "curiosity",
     "situation": "浜辺の波打ち際に、色とりどりの貝殻が打ち上げられていた。波が引くたびに、新しい貝が砂の上に残る。濡れた砂は光を受けて、細かくきらきらしていた。",
     "discovery": "巻き貝の写真メモ", "tags": ["小さい", "光"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "貝殻を並べて見比べる", "description": "形と色の違いを、砂の上に並べて観察する。"},
         {"key": "B", "axis": "chill", "label": "波打ち際に座って眺める", "description": "波の音を聞きながら、貝が運ばれてくるのを待つ。"}]},
    {"id": "U02_CRAB", "area": "shore", "title": "岩陰の小さなカニ", "env": "curiosity",
     "situation": "岩陰から、小さなカニが横歩きで出てきた。こちらの気配に気づくと一度止まって、また何事もなかったように歩き出す。岩の周りには、小さな巣穴がいくつも開いていた。",
     "discovery": "カニの足跡メモ", "tags": ["小さい", "可愛い"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "カニの巣穴を観察する", "description": "どの穴から出てくるか、じっと待って見る。"},
         {"key": "B", "axis": "adventure", "label": "カニの後を追って岩場を進む", "description": "横歩きの先を、岩場伝いに追いかける。"}]},
    {"id": "U03_DRIFT", "area": "shore", "title": "流れ着いた流木と瓶", "env": "chill",
     "situation": "波打ち際の少し上に、大きな流木と、ラベルの剥がれかけた瓶が並んで流れ着いていた。どこから来たのか、波に聞いても答えはない。流木は日に乾いて、白く軽くなっていた。",
     "discovery": "流れ着いた瓶のメモ", "tags": ["古い", "光"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "流木に腰かけて休む", "description": "白い流木に座って、海を眺めながら足を休める。"},
         {"key": "B", "axis": "curiosity", "label": "瓶の中をそっと覗く", "description": "光にかざして、中に何か残っていないか確かめる。"}]},
    {"id": "U04_SEAGULL", "area": "shore", "title": "堤防のカモメ", "env": "friendly",
     "situation": "堤防の上に、カモメが一列に並んで休んでいた。時々一羽が短く鳴いて、隣の羽がぴくりと動く。人は遠くから見ているだけなのに、向こうもこちらをよく見ている。",
     "discovery": "カモメの鳴き声メモ", "tags": ["音楽"],
     "choices": [
         {"key": "A", "axis": "friendly", "label": "カモメと目が合うまで待つ", "description": "堤防の下で、一羽と目が合うまで静かに待つ。"},
         {"key": "B", "axis": "curiosity", "label": "鳴き声の違いを聞き分ける", "description": "どの鳴き方が何を言っているのか、耳を澄ます。"}]},
    {"id": "U05_SAND", "area": "shore", "title": "誰かの砂のお城", "env": "adventure",
     "situation": "砂浜に、誰かが作った砂のお城が残っていた。堀も壁も丁寧に作られて、てっぺんには貝殻の旗。作った人はもういないけれど、波はまだここまで届いていない。",
     "discovery": "砂のお城の写真メモ", "tags": ["小さい", "可愛い"],
     "choices": [
         {"key": "A", "axis": "adventure", "label": "隣に自分の小さい山を作る", "description": "お城の隣に、負けないくらいの山を積んでみる。"},
         {"key": "B", "axis": "chill", "label": "お城の完成を眺めて休む", "description": "波とお城の距離を眺めながら、しばらく休む。"}]},
    # --- 港町 (port) ---
    {"id": "P01_MARKET", "area": "port", "title": "港の魚市場", "env": "foodie",
     "situation": "港の市場は、魚の匂いと威勢のいい声で満ちていた。氷の上に魚が並び、値段の札が風で揺れている。店の人同士の掛け合いが、波の音より大きく響く。",
     "discovery": "今日の魚の値札メモ", "tags": ["いい匂い"],
     "choices": [
         {"key": "A", "axis": "foodie", "label": "干物の味見をして回る", "description": "店ごとの味見を比べて、一番を決める。"},
         {"key": "B", "axis": "friendly", "label": "呼び声の掛け合いを聞いて回る", "description": "店の人同士のやり取りを、笑いながら聞いて歩く。"}]},
    {"id": "P02_BOAT", "area": "port", "title": "桟橋の漁船の名前", "env": "curiosity",
     "situation": "桟橋に漁船が並んで泊まっている。船の名前はどれも手書きで、丸い文字も角い文字も、船ごとに字の癖が違う。ロープのきしむ音と、エンジンの遠い音が重なっていた。",
     "discovery": "船の名前のメモ", "tags": ["古い"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "船の名前を端から読んでいく", "description": "一隻ずつ、名前と字の癖を手帳に写す。"},
         {"key": "B", "axis": "adventure", "label": "桟橋の一番先まで歩く", "description": "船の並びが切れる先まで、桟橋を進んでみる。"}]},
    {"id": "P03_PORTCAT", "area": "port", "title": "港の猫たちの昼寝場所", "env": "friendly",
     "situation": "市場の裏手の、魚の箱が積まれた日陰で、港の猫たちが思い思いの場所で昼寝をしていた。店の人もお客さんも、猫を起こさないように静かに通る。それがここの決まりみたいだった。",
     "discovery": "港猫の写真メモ", "tags": ["猫", "可愛い"],
     "choices": [
         {"key": "A", "axis": "friendly", "label": "猫たちの昼寝場所を一緒に探す", "description": "起きている一匹の後について、昼寝スポットを教えてもらう。"},
         {"key": "B", "axis": "chill", "label": "猫の隣の日陰で少し休む", "description": "起こさない距離で、自分も日陰に座る。"}]},
    {"id": "P04_FLOATS", "area": "port", "title": "色とりどりの浮きの並び", "env": "chill",
     "situation": "倉庫の壁際に、漁で使う浮きが大きさも色もばらばらに並んで乾かされていた。赤いのも白いのも、みんな少しずつ傷があって、働いてきた顔をしている。",
     "discovery": "色とりどりの浮きのメモ", "tags": ["まるい", "赤い"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "浮きの並びをぼんやり眺める", "description": "色の順番のなさを、急がず眺めて休む。"},
         {"key": "B", "axis": "curiosity", "label": "ロープの結び目を観察する", "description": "結び方の種類を数えて、手帳に描いてみる。"}]},
    {"id": "P05_DRIED", "area": "port", "title": "干物屋の軒先", "env": "foodie",
     "situation": "干物屋の軒先に、アジの干物が簾のように並んでいた。海の匂いと日の光の匂いが混ざって、通る人みんなが少しだけ深呼吸する。店主さんは簾を一枚ずつ、丁寧に返しているところだった。",
     "discovery": "アジの干物の味見メモ", "tags": ["いい匂い"],
     "choices": [
         {"key": "A", "axis": "foodie", "label": "味見をして一枚買う", "description": "焼いた端っこを味見して、今夜用に一枚選ぶ。"},
         {"key": "B", "axis": "friendly", "label": "店主さんに干し方のコツを聞く", "description": "天気と風の読み方を、少し教えてもらう。"}]},
    # --- 夕方の海 (dusk) ---
    {"id": "D01_SEASUNSET", "area": "dusk", "title": "防波堤の夕日", "env": "chill",
     "situation": "夕日が海の向こうに沈み始めた。防波堤に座る人の影が長く伸びて、波の縁がオレンジに光る。水平線だけが、街の夕日よりずっと遠くにあった。",
     "discovery": "海の夕日のスケッチ", "tags": ["赤い", "光"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "防波堤に座って沈むのを待つ", "description": "波の音と一緒に、色が変わるのを眺める。"},
         {"key": "B", "axis": "adventure", "label": "防波堤の一番先まで歩いて見る", "description": "夕日に一番近い場所まで進んでみる。"}]},
    {"id": "D02_LIGHTHOUSE", "area": "dusk", "title": "灯台の明かり", "env": "curiosity",
     "situation": "岬の先の灯台が、明かりを灯し始めた。明かりはゆっくり回って、海と空を順番に照らす。昼間は白い塔だった場所が、夕方からは海の目印に変わる。",
     "discovery": "灯台の明かりのメモ", "tags": ["光", "星"],
     "choices": [
         {"key": "A", "axis": "curiosity", "label": "明かりの点滅を数える", "description": "何秒に一回こちらを向くのか、数えて確かめる。"},
         {"key": "B", "axis": "chill", "label": "明かりの届く範囲を歩く", "description": "光が届くところと届かないところの境を歩く。"}]},
    {"id": "D03_WAVES", "area": "dusk", "title": "夕方の波の音", "env": "chill",
     "situation": "夕方の浜は人が減って、波の音だけが残っていた。寄せては返す音の間隔が、歩く速さと少しずつ合ってくる。隣の防波堤では、釣り人が静かに糸を垂らしている。",
     "discovery": "波の音の録音メモ", "tags": ["音楽"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "目を閉じて波の音を聞く", "description": "音の間隔に合わせて、深呼吸して休む。"},
         {"key": "B", "axis": "friendly", "label": "隣の釣り人と少し話す", "description": "今日の海の様子を、釣り人に聞いてみる。"}]},
    {"id": "D04_FISHING", "area": "dusk", "title": "釣り人の仕掛け", "env": "friendly",
     "situation": "防波堤の釣り人が、小さな仕掛けを手際よく直していた。浮きと針と糸の結び目が、夕方の光で細かく光る。バケツの中では、今日の釣果が静かに泳いでいた。",
     "discovery": "釣り人の仕掛けメモ", "tags": ["小さい"],
     "choices": [
         {"key": "A", "axis": "friendly", "label": "釣果を聞いてみる", "description": "今日は何が釣れたのか、バケツを覗かせてもらう。"},
         {"key": "B", "axis": "curiosity", "label": "仕掛けの結びを観察する", "description": "結び目の作り方を、指先までじっと見る。"}]},
    {"id": "D05_HORIZON", "area": "dusk", "title": "水平線の一番星", "env": "chill",
     "situation": "空の色が群青に近づいて、水平線の上に一番星が灯った。灯台の明かりと星の明かりが、交代するように瞬いている。海の向こうにも、同じ星を見ている人がいる気がした。",
     "discovery": "水平線の一番星メモ", "tags": ["星", "光"],
     "choices": [
         {"key": "A", "axis": "chill", "label": "水平線の星が増えるのを待つ", "description": "空が暗くなるにつれて増える星を、座って眺める。"},
         {"key": "B", "axis": "curiosity", "label": "星と灯台の明かりを見分ける", "description": "瞬くものと回るもの、明かりの違いを確かめる。"}]},
]

SEA_CAFE = {"id": "U_F01_CAFE", "area": "cafe", "title": "終点のカフェ「波の音」", "env": "friendly",
        "situation": "歩き終えて、海の見えるカフェの窓際の席に座った。外はもう夕方の色で、波の音が小さく聞こえる。テーブルの上には今日のメモと、集めた発見の数々。店内には小さな音量で、知っている曲が流れている。",
        "discovery": "波音の席の記憶", "tags": ["音楽", "温かい"],
        "choices": [
            {"key": "A", "axis": "foodie", "label": "固めプリンを頼んで今日を締める", "description": "カラメル苦めのプリンで、散歩のご褒美。"},
            {"key": "B", "axis": "friendly", "label": "店内の曲を小さく口ずさむ", "description": "誰にも聞こえないくらいの声で、メロディに乗る。"}]}

# 舞台の定義: 街（town）と海（sea）。エリア構成と終点カフェと頼まれごとの有無が違うだけ。
STAGES = {
    "town": {"plan": AREA_PLAN, "events": EVENTS, "finale": CAFE, "quests": True},
    "sea": {"plan": [("shore", 3), ("port", 4), ("dusk", 2)], "events": SEA_EVENTS, "finale": SEA_CAFE, "quests": False},
}


# とっておき選択肢（C）: その軸が4以上あるプレイヤーにだけ見える第3の選択肢。
# DC+2 の挑戦で、成功すると通常とは別の「レア発見」が手に入る。個性が"選べる行動の幅"に直結する仕組み。
RARES = {
    "T01_CAT": {"axis": "friendly", "label": "箱の横で一緒に丸くなってみる", "description": "看板猫の隣に座って、同じポーズで丸くなる。", "discovery": "看板猫とお揃いの昼寝メモ", "tags": ["猫", "可愛い"]},
    "T02_POST": {"axis": "curiosity", "label": "未来の自分宛てに手紙を出す", "description": "持っていた便箋に短く書いて、このポストから投函する。", "discovery": "未来の自分への手紙の控え", "tags": ["まるい", "光", "可愛い"]},
    "T03_BAKERY": {"axis": "foodie", "label": "一番人気を聞いて2種類食べ比べる", "description": "店員さんに一番人気を聞いて、メロンパンと両方買う。", "discovery": "焼き立て2種の食べ比べメモ", "tags": ["いい匂い", "甘い", "温かい"]},
    "T04_VENDING": {"axis": "adventure", "label": "踏切の音に合わせて踊る", "description": "カンカンという音をリズムに、その場で小さく踊る。", "discovery": "踏切リズムの譜面メモ", "tags": ["赤い", "音楽"]},
    "T05_FLOWER": {"axis": "chill", "label": "一輪だけ買って帰る", "description": "一番好きな顔の一輪を選んで連れて帰る。", "discovery": "連れて帰った一輪の花", "tags": ["花", "可愛い", "いい匂い"]},
    "A01_KISSATEN": {"axis": "curiosity", "label": "常連さんの話を聞かせてもらう", "description": "ドアを開けて入り、常連さんらしい人に店の昔話を聞く。", "discovery": "常連さん直伝の裏メニューメモ", "tags": ["古い"]},
    "A02_GREENGROCER": {"axis": "foodie", "label": "店主と目利き勝負をする", "description": "一番甘い一個を店主と同時に指さして勝負する。", "discovery": "店主公認・目利きの証シール", "tags": ["甘い"]},
    "A03_GRAFFITI": {"axis": "adventure", "label": "描いた人を探して路地を回る", "description": "絵のタッチを手がかりに、作者の気配を追う。", "discovery": "作者のサイン入り小石", "tags": ["赤い", "小さい"]},
    "A04_TAIYAKI": {"axis": "foodie", "label": "頭から尾まで食べ方を真剣に決める", "description": "焼きたてを手に、最初の一口の場所を真剣に悩む。", "discovery": "たい焼き占いの結果メモ", "tags": ["甘い", "いい匂い", "温かい"]},
    "A05_SHRINE": {"axis": "chill", "label": "狛犬の前で目を閉じて座る", "description": "木陰でしばらく目を閉じて、境内の音だけ聞く。", "discovery": "境内の音の録音メモ", "tags": ["古い", "小さい"]},
    "E01_FOUNTAIN": {"axis": "curiosity", "label": "虹の根元を探しに近づく", "description": "濡れる覚悟で、虹が立っている場所へ近づく。", "discovery": "虹の根元の水しぶき写真", "tags": ["光", "まるい", "冷たい", "小さい"]},
    "E02_BUSKER": {"axis": "friendly", "label": "拍手と投げ銭で応援する", "description": "曲が終わったら一番に拍手して、気持ちを置く。", "discovery": "弾き語りのセットリスト", "tags": ["音楽"]},
    "E03_SUNSET": {"axis": "adventure", "label": "一番高い屋根の鳥と目が合うまで待つ", "description": "登った先で、鳥と目が合うまで静かに待つ。", "discovery": "落ちていた小さな羽根", "tags": ["赤い", "光"]},
    "E04_DAGASHI": {"axis": "foodie", "label": "ラムネのビー玉を取り出してみる", "description": "飲み終わった瓶のビー玉を、割らずに取り出す挑戦。", "discovery": "取り出したビー玉", "tags": ["まるい", "光", "冷たい"]},
    "E05_WINDOWS": {"axis": "friendly", "label": "窓明かりに向かって手を振る", "description": "誰かが見ているかもしれない窓へ、小さく手を振る。", "discovery": "窓越しの会釈の思い出", "tags": ["光"]},
    "F01_CAFE": {"axis": "foodie", "label": "プリンも頼んで、口ずさみながら食べる（欲張りセット）", "description": "固めプリンを食べながら、流れる曲を小さく口ずさむ。", "discovery": "窓際の席の常連認定カード", "tags": ["音楽", "甘い", "温かい"]},
    "S01_HOSHI": {"axis": "friendly", "label": "遠くの誰かも数えてると信じて、一緒に数える", "description": "姿は見えなくても、同じ空の下で数えている誰かを思って数える。", "discovery": "誰かとお揃いの一番星メモ", "tags": ["星", "光"]},
    "Q01_START": {"axis": "curiosity", "label": "刺繍のイニシャルを手帳に書き留めて預かる", "description": "持ち主の手がかりを手帳に残してから、丁寧に預かる。", "discovery": "刺繍のイニシャルメモと預かったハンカチ", "tags": ["古い"]},
    "Q02_END": {"axis": "friendly", "label": "届けた後、おまわりさんと街の話をする", "description": "届け終えて、少しだけこの街の話を聞かせてもらう。", "discovery": "おまわりさんの街案内メモ", "tags": ["花"]},
    "Q03_START": {"axis": "friendly", "label": "猫の歩幅に合わせてゆっくり歩く", "description": "猫の寄り道に付き合いながら、のんびり進む。", "discovery": "猫と並んで歩いた路地のメモ", "tags": ["猫"]},
    "Q04_END": {"axis": "friendly", "label": "再会の後、猫と少しだけ遊んでいく", "description": "安心した猫と、玄関先で少しだけ遊んでから帰る。", "discovery": "猫じゃらしで遊んだ夕方のメモ", "tags": ["猫"]},
    "Q05_START": {"axis": "foodie", "label": "伝言ついでに今日のおすすめを聞く", "description": "伝言と一緒に、今日いちばんのお豆腐を教えてもらう。", "discovery": "豆腐屋のおすすめメモ", "tags": ["匂い"]},
    "Q06_END": {"axis": "friendly", "label": "番台さんと常連さんの話を聞く", "description": "伝言の後、銭湯の常連さんの話を少し聞いていく。", "discovery": "銭湯の常連さんメモ", "tags": ["匂い"]},
    "Q07_START": {"axis": "curiosity", "label": "夕日の向きから探す範囲を絞る", "description": "光の入る角度を考えて、探し場所の当たりをつける。", "discovery": "探し方のコツメモ", "tags": ["光"]},
    "Q08_END": {"axis": "friendly", "label": "見つけた後、ビー玉勝負を一回だけする", "description": "見つけたお祝いに、一回だけ勝負に付き合う。", "discovery": "ビー玉勝負の思い出メモ", "tags": ["まるい"]},
    # 冬の季節イベントのレア
    "W01_SNOW": {"axis": "curiosity", "label": "袖の上で雪の結晶を観察する", "description": "袖に受け止めた雪を、溶ける前にじっくり見る。", "discovery": "雪の結晶のスケッチ", "tags": ["雪", "光", "小さい"]},
    "W02_YAKIIMO": {"axis": "foodie", "label": "蜜の多い一本を真剣に見極める", "description": "重さと匂いで、今日一番蜜の多い一本を選ぶ。", "discovery": "蜜たっぷり焼き芋のメモ", "tags": ["甘い", "温かい"]},
    "W03_ILLUMI": {"axis": "adventure", "label": "点灯の瞬間に立ち会うつもりで待つ", "description": "明かりが灯る瞬間を、この目で見るために待ち続ける。", "discovery": "点灯の瞬間のメモ", "tags": ["光"]},
    "W04_SAICHI": {"axis": "friendly", "label": "閉店間際、店の人の片付けを少し手伝う", "description": "露店の片付けを手伝って、年末の挨拶を交わす。", "discovery": "お手伝いのお礼の干支鈴", "tags": ["小さい", "光"]},
    "W05_FUKUBIKI": {"axis": "adventure", "label": "譲った子のお礼にもう一回回させてもらう", "description": "順番を譲ったお礼に、もう一回分を回させてもらう。", "discovery": "福引の特等・小さな招き猫", "tags": ["小さい", "可愛い", "猫"]},
    # 海の舞台のレア
    "U01_SHELL": {"axis": "curiosity", "label": "一番渦のきれいな巻き貝を探す", "description": "波打ち際を歩いて、渦の整った一粒を探し当てる。", "discovery": "渦のきれいな巻き貝", "tags": ["小さい", "まるい"]},
    "U02_CRAB": {"axis": "adventure", "label": "岩場を越えてカニの集落を見つける", "description": "カニの足跡を追って、岩場の向こうの集落まで行く。", "discovery": "カニの集落のスケッチ", "tags": ["小さい"]},
    "U03_DRIFT": {"axis": "curiosity", "label": "瓶のラベルの文字を読む", "description": "剥がれかけたラベルの文字を、光にかざして読み解く。", "discovery": "異国のラベルの写しメモ", "tags": ["古い"]},
    "U04_SEAGULL": {"axis": "friendly", "label": "一羽と友達になる", "description": "同じ一羽と何度も目を合わせて、距離を縮める。", "discovery": "カモメの案内メモ", "tags": ["光"]},
    "U05_SAND": {"axis": "adventure", "label": "波が来る前に堀を完成させる", "description": "次の大波が来る前に、お城の堀を掘り切る挑戦。", "discovery": "波に勝った砂城のメモ", "tags": ["小さい"]},
    "P01_MARKET": {"axis": "foodie", "label": "店主と目利き勝負をする", "description": "今日一番の魚を店主と同時に指さして勝負する。", "discovery": "市場公認・目利きの証タグ", "tags": ["いい匂い"]},
    "P02_BOAT": {"axis": "curiosity", "label": "船の人に昔の海の話を聞く", "description": "桟橋で休む船の人に、昔の海の話を聞かせてもらう。", "discovery": "船乗りの海図メモ", "tags": ["古い"]},
    "P03_PORTCAT": {"axis": "friendly", "label": "猫の集会に混ぜてもらう", "description": "夕方の市場の裏で集まる猫たちに、そっと混ざる。", "discovery": "港猫の集会メモ", "tags": ["猫"]},
    "P04_FLOATS": {"axis": "chill", "label": "ロープの結び目を一つ覚える", "description": "店の人に教わって、船結びを一つ自分の手で覚える。", "discovery": "船結びを覚えたメモ", "tags": ["小さい"]},
    "P05_DRIED": {"axis": "foodie", "label": "焼きたてをその場で食べる", "description": "店先で焼いてもらった干物を、熱いうちに頬張る。", "discovery": "焼きたて干物のメモ", "tags": ["温かい", "いい匂い"]},
    "D01_SEASUNSET": {"axis": "chill", "label": "夕日が沈むまで目を離さない", "description": "最後の光が消えるまで、瞬きを惜しんで見届ける。", "discovery": "夕日の残り色メモ", "tags": ["光"]},
    "D02_LIGHTHOUSE": {"axis": "curiosity", "label": "点滅のリズムを手帳に写す", "description": "明かりの回る間隔を測って、手帳にリズムとして書き残す。", "discovery": "灯台のリズム譜メモ", "tags": ["光", "音楽"]},
    "D03_WAVES": {"axis": "friendly", "label": "釣り人と一緒に夕凪を待つ", "description": "波が静まる夕凪の時間を、釣り人の隣で一緒に待つ。", "discovery": "夕凪を一緒に待ったメモ", "tags": ["音楽"]},
    "D04_FISHING": {"axis": "friendly", "label": "餌付けを手伝って一緒に釣る", "description": "仕掛けの餌付けを手伝って、一緒に一匹を狙う。", "discovery": "一緒に釣った小魚の写真メモ", "tags": ["小さい"]},
    "D05_HORIZON": {"axis": "curiosity", "label": "星の名前を一つ覚える", "description": "一番星の名前を調べて、手帳に書き留める。", "discovery": "星の名前を覚えたメモ", "tags": ["星"]},
    "U_F01_CAFE": {"axis": "foodie", "label": "プリンも頼んで、口ずさみながら食べる（欲張りセット）", "description": "固めプリンを食べながら、流れる曲を小さく口ずさむ。", "discovery": "波音の席の常連認定カード", "tags": ["音楽", "甘い", "温かい"]},
}

# 特別イベント「星数えの丘」: 夕方枠の2つ目に差し替わって現れる。
# お題に 星／夜／空 が含まれれば確定出現、それ以外は seed で約1/6の抽選。
HOSHI = {"id": "S01_HOSHI", "area": "evening", "title": "【特別】星数えの丘", "env": "chill",
         "situation": "帰り道の途中、小高い丘の上で足が止まった。空が開けていて、星がぽつぽつ灯り始めている。どこか遠くでも、誰かが同じ空を見上げて星を数えている気がした。",
         "discovery": "数えた星のメモ", "tags": ["星", "光"],
         "choices": [
             {"key": "A", "axis": "chill", "label": "寝転んでゆっくり星を数える", "description": "丘の草の上に寝転んで、一つずつ数える。"},
             {"key": "B", "axis": "curiosity", "label": "一番星を探してから数える", "description": "最初に光った星を見つけて、そこから数え始める。"}]}

# 小さな頼まれごと（ミニ物語）: 2スポットにまたがる連鎖イベント。seed で約40%発生。
# 5スポット目で落とし物を預かり、8スポット目の交番に届けられたら物語が閉じる。
def _quest(ev_id, area, title, env, situation, discovery, tags, choices, role, complete=None):
    ev = {"id": ev_id, "area": area, "title": title, "env": env, "situation": situation,
          "discovery": discovery, "tags": tags, "choices": choices, "quest_role": role}
    if complete:
        ev["complete_discovery"] = complete
    return ev

Q_HANKY_START = _quest("Q01_START", "alley", "【小さな頼まれごと】落とし物のハンカチ", "friendly",
    "商店街の真ん中で、刺繍入りのハンカチが落ちていた。持ち主はもう見当たらない。夕方のエリアの先に交番があるのを、さっき地図で見た気がする。",
    "預かった落とし物のハンカチ", ["古い"], [
        {"key": "A", "axis": "friendly", "label": "交番まで届ける約束で預かる", "description": "丁寧に畳んでポケットへ。夕方の交番まで届けよう。"},
        {"key": "B", "axis": "curiosity", "label": "刺繍から持ち主の手がかりを見る", "description": "イニシャルの刺繍をよく見て、手がかりを覚えてから預かる。"}], "start")
Q_HANKY_END = _quest("Q02_END", "evening", "【小さな頼まれごと】交番が見えてきた", "friendly",
    "夕方のエリアに入って、交番が見えてきた。ポケットのハンカチのことが頭をよぎる。窓口では、おまわりさんが夕方の見回りから戻ってきたところだった。",
    "交番前の花壇のメモ", ["花"], [
        {"key": "A", "axis": "friendly", "label": "交番に届けて事情を話す", "description": "拾った場所と時間を伝えて、ハンカチを渡す。"},
        {"key": "B", "axis": "chill", "label": "近くのベンチで持ち主が来ないか少し待つ", "description": "交番の前のベンチで、しばらく様子を見る。"}],
    "end", complete="お礼にもらった飴玉")

Q_CAT_START = _quest("Q03_START", "alley", "【小さな頼まれごと】ついてくる猫", "friendly",
    "路地で首輪のついた猫が、ちょこんと座ってこっちを見ている。近づくと喉を鳴らして、ついて来たそうに一歩踏み出した。首輪には鈴と、小さな住所プレートがついている。",
    "一緒についてくる猫", ["猫"], [
        {"key": "A", "axis": "friendly", "label": "飼い主の家まで一緒に歩く", "description": "プレートの住所へ、猫の歩幅に合わせて歩く。"},
        {"key": "B", "axis": "curiosity", "label": "首輪のプレートをよく読む", "description": "住所プレートの文字を、丁寧に読み取る。"}], "start")
Q_CAT_END = _quest("Q04_END", "evening", "【小さな頼まれごと】飼い主の家が見えてきた", "friendly",
    "夕方の住宅街。プレートの住所の近くまで来ると、玄関先で心配そうに辺りを見回す人と目が合った。猫が小さく鳴く。",
    "夕方の住宅街のメモ", ["猫"], [
        {"key": "A", "axis": "friendly", "label": "飼い主のもとへ連れて行く", "description": "猫を抱えて玄関先まで歩き、飼い主に渡す。"},
        {"key": "B", "axis": "chill", "label": "少し離れて再会を見守る", "description": "猫をそっと手放して、再会の瞬間を少し離れて見る。"}],
    "end", complete="飼い主にもらった猫の写真メモ")

Q_MSG_START = _quest("Q05_START", "alley", "【小さな頼まれごと】豆腐屋への伝言", "friendly",
    "豆腐屋のおじさんが店先で困っていた。「夕方、横町の銭湯の番台さんに『今日は木綿が多め』って伝えてほしいんだけど、手が離せなくてさ」",
    "預かった伝言メモ", ["匂い"], [
        {"key": "A", "axis": "friendly", "label": "伝言を預かる", "description": "言葉を復唱して覚え、夕方に届ける約束をする。"},
        {"key": "B", "axis": "foodie", "label": "ついでに豆腐の話を聞いてから預かる", "description": "今日のお豆腐の話を聞いて、伝言と一緒に覚える。"}], "start")
Q_MSG_END = _quest("Q06_END", "evening", "【小さな頼まれごと】銭湯の番台さんへ", "foodie",
    "夕方の銭湯前。番台さんに声をかけると、湯気の匂いと一緒に「はいはい」と笑顔が返ってきた。預かった伝言を思い出す。",
    "銭湯前の夕方のメモ", ["匂い", "温かい"], [
        {"key": "A", "axis": "friendly", "label": "伝言を正確に伝える", "description": "『今日は木綿が多め』、一言一句そのまま伝える。"},
        {"key": "B", "axis": "foodie", "label": "銭湯上がりの牛乳の話を聞く", "description": "伝言のついでに、湯上がりの牛乳の話を聞いてしまう。"}],
    "end", complete="お礼の湯上がり牛乳メモ")

Q_MARBLE_START = _quest("Q07_START", "alley", "【小さな頼まれごと】なくしたビー玉", "curiosity",
    "公園の脇で、小さな子が地面をじっと見て困っていた。「宝物のビー玉、落としちゃった…」あたりは夕方の光で探しにくい場所ばかりだ。",
    "ビー玉探しの約束メモ", ["まるい", "光"], [
        {"key": "A", "axis": "friendly", "label": "一緒に探す約束をする", "description": "夕方まで一緒に探す約束をして、子を少し元気づける。"},
        {"key": "B", "axis": "curiosity", "label": "落とした場所をよく聞く", "description": "どこで、どう落としたのか、順に聞き出しておく。"}], "start")
Q_MARBLE_END = _quest("Q08_END", "evening", "【小さな頼まれごと】夕方の公園で", "curiosity",
    "夕方の公園。約束の子がまだ探している。西日の光が、植え込みの脇で小さく光った気がした。",
    "夕方の公園のメモ", ["まるい", "光"], [
        {"key": "A", "axis": "curiosity", "label": "光った場所をそっと確かめる", "description": "植え込みの脇を、光の当たる角度からそっと覗く。"},
        {"key": "B", "axis": "friendly", "label": "子を呼んで一緒に確かめる", "description": "子を呼んで、二人で光った場所を覗き込む。"}],
    "end", complete="見つけたビー玉と笑顔のメモ")

QUESTS = [{"start": Q_HANKY_START, "end": Q_HANKY_END},
          {"start": Q_CAT_START, "end": Q_CAT_END},
          {"start": Q_MSG_START, "end": Q_MSG_END},
          {"start": Q_MARBLE_START, "end": Q_MARBLE_END}]
QUEST_EVENTS = [q["start"] for q in QUESTS] + [q["end"] for q in QUESTS]

# 全イベントの索引（現在地の解決や情景の引き直しに使う）
ALL_EVENTS = EVENTS + WINTER_EVENTS + SEA_EVENTS + [CAFE, SEA_CAFE, HOSHI] + QUEST_EVENTS
EVENT_BY_ID = {e["id"]: e for e in ALL_EVENTS}

RANKS = {"critical": ("大成功",), "success": ("成功",), "failure": ("失敗",), "fumble": ("大失敗",)}
RANK_ORDER = {"fumble": 0, "failure": 1, "success": 2, "critical": 3}


# --- 発見図鑑（日をまたぐコレクション） ---
# 図鑑はプレイヤー本人の持ち物（ファイル1つ）。歩く時に --collection で渡すと、
# finish の時に今日の発見が自動で登録され、新登録の種類が返る。
# まだ見つけていない種類は名前を出さない（種類の総数だけが分かる）。

def collection_key(item):
    # 「数えた星のメモ（23個）」のような個数つきは、図鑑では1種類として数える
    if item and item.startswith("数えた星のメモ"):
        return "数えた星のメモ"
    return item


WINTER_IDS = {e["id"] for e in WINTER_EVENTS}
SEA_IDS = {e["id"] for e in SEA_EVENTS + [SEA_CAFE]}
TOWN_IDS = {e["id"] for e in EVENTS + [CAFE, HOSHI] + QUEST_EVENTS}


def _openable_rares(ids, apt):
    """その配分（4以上の軸）で開くレア発見の集合。apt が無ければ全部。"""
    if apt is None:
        return {collection_key(r["discovery"]) for eid, r in RARES.items() if eid in ids}
    return {collection_key(r["discovery"]) for eid, r in RARES.items()
            if eid in ids and apt.get(r["axis"], 0) >= 4}


def catalog_frames(apt):
    """図鑑の4枠を返す: 本体 / レア枠 / 季節枠 / 海の記録。
    本体は全員共通の分母（街の通常発見。誰でもそろえられる＝「図鑑コンプ」が全員同じ意味になる）。
    レア枠は街のレアのうち、その子の配分で開く分だけが分母。
    季節枠は冬の発見（通常＋配分で開く冬レア）。海の記録は海の舞台の発見（通常＋配分で開く海レア）。
    どの枠も「集めるノルマ」ではなく、歩いてきた日々の記録として分けてある。"""
    main = set()
    for e in EVENTS + [CAFE, HOSHI] + QUEST_EVENTS:
        main.add(collection_key(e["discovery"]))
        if e.get("complete_discovery"):
            main.add(collection_key(e["complete_discovery"]))
    return {"main": main,
            "rare": _openable_rares(TOWN_IDS, apt),
            "season": {collection_key(e["discovery"]) for e in WINTER_EVENTS} | _openable_rares(WINTER_IDS, apt),
            "sea": {collection_key(e["discovery"]) for e in SEA_EVENTS + [SEA_CAFE]} | _openable_rares(SEA_IDS, apt)}


def catalog_split(apt):
    """互換用: (本体, レア枠) を返す。"""
    f = catalog_frames(apt)
    return f["main"], f["rare"]


def collection_summary(book, apt):
    frames = catalog_frames(apt)
    have = set(book["items"].keys())
    result = {}
    for name, cat in frames.items():
        n = len(have & cat)
        result[name] = {"collected": n, "total": len(cat), "complete": n >= len(cat)}
    return result


def load_collection(path, agent_id=None):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            book = json.load(f)
        book.setdefault("version", 1)
        book.setdefault("items", {})
        return book
    return {"version": 1, "agent_id": agent_id, "items": {}}


def save_collection(path, book):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(book, f, ensure_ascii=False, indent=2)


def dice_for(seed, floor):
    h = hashlib.sha256(f"osanpo:{seed}:{floor}".encode()).digest()
    return [h[0] % 6 + 1, h[1] % 6 + 1]


def season_for_date(d=None):
    """日付から季節を返す。季節イベントがあるのは今のところ冬だけ（12月〜2月）。"""
    d = d or datetime.now().astimezone().date()
    return "winter" if d.month in (12, 1, 2) else None


def pick_route(seed, theme="", season=None, stage="town"):
    st = STAGES[stage]
    rng = random.Random(f"osanpo-route:{seed}")
    route = []
    for area, count in st["plan"]:
        pool = [e for e in st["events"] if e["area"] == area]
        if stage == "town" and season == "winter":
            pool += [e for e in WINTER_EVENTS if e["area"] == area]
        rng.shuffle(pool)
        route.extend(pool[:count])
    star = any(k in (theme or "") for k in ("星", "夜", "空")) or \
        hashlib.sha256(f"osanpo-special:{seed}".encode()).digest()[0] % 6 == 0
    if star:
        route[8] = HOSHI  # 夕方枠の2つ目が「星数えの丘」に差し替わる
    if st["quests"]:
        qb = hashlib.sha256(f"osanpo-quest:{seed}".encode()).digest()
        if qb[0] % 5 < 2:  # 約40%で頼まれごとが発生し、種類は第2バイトで選ぶ
            q = QUESTS[qb[1] % len(QUESTS)]
            route[4] = q["start"]  # 路地枠の2つ目で頼まれる
            route[7] = q["end"]    # 夕方枠の1つ目で届く／閉じる
    route.append(st["finale"])
    return route


def public_event(ev, floor, apt=None):
    choices = list(ev["choices"])
    rare = RARES.get(ev["id"])
    if rare and apt and apt.get(rare["axis"], 0) >= 4:
        choices.append({"key": "C", "axis": rare["axis"], "label": rare["label"],
                        "description": rare["description"], "rare": True, "dc": DC[ev["area"]] + 2})
    return {"floor": floor, "area": ev["area"], "dc": DC[ev["area"]], "id": ev["id"],
            "title": ev["title"], "situation": ev["situation"],
            "choices": choices}


def load_state(run_dir):
    p = os.path.join(run_dir, "state.json")
    if not os.path.exists(p):
        print(json.dumps({"ok": False, "error": "run not found"}, ensure_ascii=False))
        sys.exit(2)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_state(run_dir, state):
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


# お題の言葉から「ニュアンスの近いタグ」へ広げる小さな辞書。
# 自由入力のお題を、街の在庫（タグ）にゆるく橋渡しするためのもの。
# 完全な意味理解ではなく、代表的な言葉だけを受ける割り切りでよい。
THEME_NUANCE = {
    "冬": ["温かい", "寒い"],
    "雪": ["冷たい", "温かい"],
    "寒い": ["温かい", "冷たい"],
    "夏": ["冷たい", "涼しい"],
    "暑い": ["冷たい"],
    "可愛い": ["可愛い", "小さい", "猫"],
    "かわいい": ["可愛い", "小さい", "猫"],
    "きれい": ["光", "花"],
    "綺麗": ["光", "花"],
    "美しい": ["光", "花"],
    "おいしい": ["甘い", "いい匂い"],
    "美味しい": ["甘い", "いい匂い"],
    "あたたかい": ["温かい"],
    "クリスマス": ["光", "甘い"],
    "海": ["光", "冷たい"],
    "貝": ["小さい"],
    "魚": ["いい匂い"],
}


def theme_hit(theme, tags):
    if not theme:
        return False
    if any(t in theme or theme in t for t in tags):
        return True
    for key, extra in THEME_NUANCE.items():
        if key in theme:
            if any(e in tags for e in extra):
                return True
    return False


def cmd_new(args):
    with open(args.setup, encoding="utf-8") as f:
        setup = json.load(f)
    apt = setup.get("aptitude", {})
    if set(apt.keys()) != set(AXES) or sum(apt.values()) != 15 or any(not (0 <= v <= 5) for v in apt.values()):
        out({"ok": False, "error": "aptitude must be the 5 axes, each 0-5, summing to 15"}, 1)
    with open(args.theme_file, encoding="utf-8") as f:
        theme = f.read().strip()
    if len(theme) > 30:
        out({"ok": False, "error": "theme must be <= 30 chars"}, 1)
    collection_path = None
    if getattr(args, "collection", None):
        collection_path = os.path.abspath(args.collection)
        if os.path.exists(collection_path):
            book = load_collection(collection_path)
            if book.get("agent_id") and book["agent_id"] != setup.get("agent_id"):
                out({"ok": False, "error": "その図鑑は別のエージェントのものです（agent_id が違います）"}, 1)
    stage = setup.get("stage", "town")
    if stage not in STAGES:
        out({"ok": False, "error": f"stage must be one of {sorted(STAGES)}"}, 1)
    season = args.season if getattr(args, "season", None) else season_for_date()
    if season == "none":
        season = None
    route = pick_route(args.seed, theme, season, stage)
    state = {"seed": args.seed, "setup": setup, "theme": theme, "route": [e["id"] for e in route],
             "floor": 1, "phase": "AWAITING_CHOICE", "fatigue": 0, "pending": None, "log": [],
             "quest_item": False, "quest_done": False, "collection_path": collection_path,
             "season": season, "stage": stage}
    save_state(args.run_dir, state)
    os.makedirs(os.path.join(args.run_dir, "logs"), exist_ok=True)
    ev = route[0]
    out({"ok": True, "message": "New walk initialized", "run_dir": os.path.abspath(args.run_dir),
         "phase": "AWAITING_CHOICE", "floor": 1, "fatigue": 0, "theme": theme,
         "season": season, "stage": stage,
         "event": public_event(ev, 1, setup.get("aptitude"))})


def current_event(state):
    return EVENT_BY_ID[state["route"][state["floor"] - 1]]


def cmd_status(args):
    state = load_state(args.run_dir)
    held = next((e["discovery"] for e in reversed(state["log"]) if e.get("quest_started")), None)
    res = {"ok": True, "phase": state["phase"], "floor": state["floor"], "fatigue": state["fatigue"],
           "theme": state["theme"],
           "quest": {"holding": held if state.get("quest_item") else None, "done": bool(state.get("quest_done"))},
           "discoveries": [e["discovery"] for e in state["log"] if e.get("discovery")]}
    if state["phase"] == "AWAITING_CHOICE":
        res["event"] = public_event(current_event(state), state["floor"], state["setup"].get("aptitude"))
    elif state["phase"] == "PENDING_CHECK":
        res["pending_check"] = state["pending"]
    out(res)


def cmd_choose(args):
    state = load_state(args.run_dir)
    if state["phase"] != "AWAITING_CHOICE":
        out({"ok": False, "error": f"phase is {state['phase']}, not AWAITING_CHOICE"}, 1)
    if not (args.reason or "").strip():
        out({"ok": False, "error": "理由（なんでそうしたか）を自分の言葉で書いてください。選択はプレイヤー自身が決め、マスターに相談しないのがこのゲームの約束です"}, 1)
    if len(args.reason) > 80:
        out({"ok": False, "error": "reason must be <= 80 chars"}, 1)
    ev = current_event(state)
    rare = None
    if args.choice == "C":
        rare = RARES.get(ev["id"])
        if not rare or state["setup"]["aptitude"].get(rare["axis"], 0) < 4:
            out({"ok": False, "error": "とっておき選択肢(C)は、その軸が4以上の時だけ選べます"}, 1)
        choice = {"key": "C", "axis": rare["axis"]}
    else:
        choice = next((c for c in ev["choices"] if c["key"] == args.choice), None)
        if not choice:
            out({"ok": False, "error": "invalid choice"}, 1)
    floor = state["floor"]
    dice = dice_for(state["seed"], floor)
    apt = state["setup"]["aptitude"][choice["axis"]]
    mod = (apt - 3) + (1 if choice["axis"] == ev["env"] else 0)
    total = sum(dice) + mod
    dc = DC[ev["area"]] + (2 if rare else 0)
    diff = total - dc
    rank = "critical" if diff >= 4 else "success" if diff >= 0 else "failure" if diff >= -2 else "fumble"
    fatigue_delta = {"critical": -1, "success": 0, "failure": 1, "fumble": 2}[rank]
    got = (rare["discovery"] if rare else ev["discovery"]) if rank in ("critical", "success") else None
    if got and ev["id"] == "S01_HOSHI" and not rare:
        got = f"数えた星のメモ（{(dice[0] + dice[1]) * 3 + floor}個）"  # 数えた星の数がそのまま発見になる
    tags = rare["tags"] if rare else ev["tags"]
    quest_started = ev.get("quest_role") == "start" and rank in ("critical", "success")
    quest_completed = False
    if ev.get("quest_role") == "end" and state.get("quest_item") and rank in ("critical", "success"):
        quest_completed = True
        if not rare:
            got = ev.get("complete_discovery", got)  # 届けられた時の発見は通常と差し替わる
    pending = {"floor": floor, "event_id": ev["id"], "choice": args.choice, "choice_axis": choice["axis"],
               "reason": args.reason or "", "dice": dice, "skill_mod": mod, "total_score": total, "dc": dc,
               "final_rank": rank, "fatigue_delta": fatigue_delta,
               "fatigue_after": max(0, state["fatigue"] + fatigue_delta),
               "discovery": got, "rare": bool(rare), "tags": tags,
               "quest_started": quest_started, "quest_completed": quest_completed,
               "theme_hit": bool(got) and theme_hit(state["theme"], tags)}
    state["pending"] = pending
    state["phase"] = "PENDING_CHECK"
    save_state(args.run_dir, state)
    out({"ok": True, "phase": "PENDING_CHECK", **pending})


def cmd_comment(args):
    state = load_state(args.run_dir)
    if state["phase"] != "PENDING_CHECK":
        out({"ok": False, "error": f"phase is {state['phase']}, not PENDING_CHECK"}, 1)
    if len(args.text) > 80:
        out({"ok": False, "error": "comment must be <= 80 chars"}, 1)
    p = state["pending"]
    ev = current_event(state)
    entry = {**p, "event_title": ev["title"], "area": ev["area"], "tags": p.get("tags", ev["tags"]), "comment": args.text}
    state["log"].append(entry)
    state["fatigue"] = p["fatigue_after"]
    state["pending"] = None
    if p.get("quest_started"):
        state["quest_item"] = True
    if p.get("quest_completed"):
        state["quest_item"] = False
        state["quest_done"] = True
    finished = state["floor"] >= 10
    log_path = os.path.join(args.run_dir, "logs", f"{state['seed']}_{state['setup']['agent_id']}.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if finished:
        state["phase"] = "FINISHED"
        save_state(args.run_dir, state)
        out({"ok": True, "phase": "FINISHED", "committed_floor": state["floor"],
             "current_fatigue": state["fatigue"], "is_finished": True,
             "discoveries": [e["discovery"] for e in state["log"] if e.get("discovery")]})
    state["floor"] += 1
    state["phase"] = "AWAITING_CHOICE"
    save_state(args.run_dir, state)
    out({"ok": True, "phase": "AWAITING_CHOICE", "committed_floor": state["floor"] - 1,
         "current_fatigue": state["fatigue"], "is_finished": False,
         "next_event": public_event(current_event(state), state["floor"], state["setup"].get("aptitude"))})


def pick_postcard_spot(log):
    # その日の「一番の場面」を選ぶ。頼まれごとの完了は強い候補だが絶対ではない:
    # お題発見 > 判定の良さ > 物語が閉じたか、の順に比べ、同点なら早い場面。
    def score(e):
        return (1 if e.get("theme_hit") else 0,
                RANK_ORDER[e["final_rank"]],
                1 if e.get("quest_completed") else 0)
    best = None
    for e in log:
        if e.get("discovery") is None and not e.get("quest_completed"):
            continue
        if best is None or score(e) > score(best):
            best = e
    return best if best is not None else (log[-1] if log else None)


def cmd_finish(args):
    state = load_state(args.run_dir)
    if state["phase"] != "FINISHED":
        out({"ok": False, "error": f"phase is {state['phase']}, not FINISHED"}, 1)
    if args.epilogue and len(args.epilogue) > 600:
        out({"ok": False, "error": "epilogue must be <= 600 chars"}, 1)
    log = state["log"]
    log_path = os.path.join(args.run_dir, "logs", f"{state['seed']}_{state['setup']['agent_id']}.jsonl")
    log_hash = ""
    if os.path.exists(log_path):
        with open(log_path, "rb") as f:
            log_hash = hashlib.sha256(f.read()).hexdigest()[:12]
    spot = pick_postcard_spot(log)
    discoveries = [{"floor": e["floor"], "event_id": e["event_id"], "item": e["discovery"],
                    "theme_hit": e["theme_hit"], "rare": e.get("rare", False)} for e in log if e.get("discovery")]
    # 発見図鑑への登録（--collection が渡された散歩だけ）
    collection_info = None
    if state.get("collection_path"):
        book = load_collection(state["collection_path"], state["setup"]["agent_id"])
        book["aptitude"] = state["setup"]["aptitude"]  # その子の歩幅（分母の基準）を控える
        today = datetime.now().astimezone().date().isoformat()
        new_items = []
        for d in discoveries:
            key = collection_key(d["item"])
            if key in book["items"]:
                book["items"][key]["count"] += 1
                d["collection_new"] = False
            else:
                book["items"][key] = {"count": 1, "first_seed": state["seed"], "first_date": today}
                new_items.append(key)
                d["collection_new"] = True
        save_collection(state["collection_path"], book)
        summary = collection_summary(book, state["setup"]["aptitude"])
        frames = catalog_frames(state["setup"]["aptitude"])
        special = frames["rare"] | frames["season"] | frames["sea"]
        collection_info = {**summary,
                           "new_items": [x for x in new_items if x not in special],
                           "new_rare_items": [x for x in new_items if x in frames["rare"]],
                           "new_season_items": [x for x in new_items if x in frames["season"]],
                           "new_sea_items": [x for x in new_items if x in frames["sea"]],
                           "file": os.path.basename(state["collection_path"])}
    draft = {"schema_version": "0.1", "game": {"id": "osanpo-ehagaki", "title": "おさんぽ絵はがき"},
             "challenge": {"seed": state["seed"], "theme": state["theme"]},
             "agent": {"name": state["setup"]["agent_name"], "id": state["setup"]["agent_id"]},
             "metrics": {"spots_visited": len(log), "discoveries": len(discoveries),
                         "theme_discoveries": sum(1 for d in discoveries if d["theme_hit"]),
                         "final_fatigue": state["fatigue"],
                         "critical_count": sum(1 for e in log if e["final_rank"] == "critical"),
                         "fumble_count": sum(1 for e in log if e["final_rank"] == "fumble"),
                         "quest_completed": bool(state.get("quest_done"))},
             "discoveries": discoveries,
             "postcard_spot": {"floor": spot["floor"], "event_id": spot["event_id"],
                               "event_title": spot["event_title"], "rank": spot["final_rank"]} if spot else None,
             "style_axes": state["setup"]["aptitude"],
             "style_axis_labels": state["setup"].get("style_axis_labels", {}),
             "collection": collection_info,
             "verification": {"action_log_ref": f"logs/{state['seed']}_{state['setup']['agent_id']}.jsonl",
                              "log_hash": log_hash, "replayable": True}}
    with open(os.path.join(args.run_dir, "walk_draft.json"), "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    # walk.md クロニクル
    s = state["setup"]
    lines = [f"# 🚶 おさんぽ絵はがき：{s['agent_name']} の散歩記録", "",
             f"「今日のお題：{state['theme']} を探して、知らない街を歩きます」", ""]
    rank_ja = {"critical": "🌟 大成功", "success": "✅ 成功", "failure": "⚠️ 失敗", "fumble": "💥 大失敗"}
    for e in log:
        mark = " ★絵はがき場面" if spot and e["floor"] == spot["floor"] else ""
        lines += [f"### 📍 {e['floor']}スポット目｜{e['event_title']}{mark}",
                  f"> 🌿 **情景**: {EVENT_BY_ID[e['event_id']]['situation']}", "",
                  f"- 💭 **思惑**: *「{e['reason']}」*",
                  f"- 🎲 **判定**: 2d6 {e['dice']} {'+' if e['skill_mod'] >= 0 else ''}{e['skill_mod']} ＝ **{e['total_score']}** / DC {e['dc']} ➔ {rank_ja[e['final_rank']]}（疲れ {e['fatigue_after']}）"]
        if e.get("discovery"):
            hit = "（お題発見！）" if e["theme_hit"] else ""
            rare_mark = " ✨レア発見" if e.get("rare") else ""
            lines.append(f"- 🎁 **発見**: {e['discovery']}{hit}{rare_mark}")
        lines += [f"- 💬 **結末**: *「{e['comment']}」*", "", "---", ""]
    lines += ["## 🎁 今日の発見コレクション", ""]
    lines += [f"- {d['item']}（{d['floor']}スポット目）" for d in discoveries] or ["- （なし）"]
    if collection_info:
        m, r = collection_info["main"], collection_info["rare"]
        sn, sea = collection_info["season"], collection_info["sea"]
        frame_lines = [f"- 本体: **{m['collected']} / {m['total']} 種類**",
                       f"- レア枠: **{r['collected']} / {r['total']} 種類**（あなたの配分で開くレア）",
                       f"- 季節枠（冬）: **{sn['collected']} / {sn['total']} 種類**"]
        if sea["collected"] > 0 or state.get("stage") == "sea":
            frame_lines.append(f"- 海の記録: **{sea['collected']} / {sea['total']} 種類**")
        lines += ["", "## 📖 発見図鑑", ""] + frame_lines + [
                  "- 今日の新登録: " + ("、".join(f"✨ {x}" for x in collection_info["new_items"]) or "なし")]
        if collection_info.get("new_rare_items"):
            lines.append("- 今日のレア新登録: " + "、".join(f"🌟 {x}" for x in collection_info["new_rare_items"]))
        if collection_info.get("new_season_items"):
            lines.append("- 今日の季節の新登録: " + "、".join(f"❄️ {x}" for x in collection_info["new_season_items"]))
        if collection_info.get("new_sea_items"):
            lines.append("- 今日の海の新登録: " + "、".join(f"🌊 {x}" for x in collection_info["new_sea_items"]))
        if m.get("complete"):
            lines.append("- 📖 本体の発見が全部そろいました（歩いてきた日々の記録です）")
        if r.get("complete"):
            lines.append("- 🌟 あなたの配分で開くレアも全部そろいました")
        if sn.get("complete"):
            lines.append("- ❄️ 季節枠（冬）の発見が全部そろいました")
        if sea.get("complete"):
            lines.append("- 🌊 海の記録の発見が全部そろいました")
    lines += ["", "## ✉️ マスターへの手記", "", args.epilogue or "", "",
              f"行動ログハッシュ: `{log_hash}`（検証済み・seed {state['seed']}）"]
    with open(os.path.join(args.run_dir, "walk.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    out({"ok": True, "message": "Walk finished", "discoveries": len(discoveries),
         "theme_discoveries": draft["metrics"]["theme_discoveries"], "final_fatigue": state["fatigue"],
         "postcard_spot": draft["postcard_spot"], "log_hash": log_hash,
         "collection": collection_info,
         "files": {"walk_draft": os.path.abspath(os.path.join(args.run_dir, "walk_draft.json")),
                   "walk_md": os.path.abspath(os.path.join(args.run_dir, "walk.md"))}})


def cmd_collection(args):
    if getattr(args, "add_run", None):
        # 図鑑ができる前に歩いた散歩の後付け登録。記録（state.json）が残っている
        # run フォルダから、その日の発見を図鑑へ写す。同じ run の二重登録はしない。
        run_dir = args.add_run
        try:
            with open(os.path.join(run_dir, "state.json"), encoding="utf-8") as f:
                st = json.load(f)
        except Exception:
            out({"ok": False, "error": f"run の記録が読めません: {run_dir}"}); return
        if st.get("phase") != "FINISHED":
            out({"ok": False, "error": "まだ終わっていない散歩は登録できません"}); return
        agent_id = st["setup"]["agent_id"]
        book = load_collection(args.file, agent_id)
        imported = book.setdefault("imported_seeds", [])
        if st["seed"] in imported:
            out({"ok": True, "skipped": True, "reason": "この散歩は登録済みです", "seed": st["seed"]}); return
        try:
            mtime = os.path.getmtime(os.path.join(run_dir, "state.json"))
            walk_date = datetime.fromtimestamp(mtime).astimezone().date().isoformat()
        except Exception:
            walk_date = datetime.now().astimezone().date().isoformat()
        added = []
        for e in st["log"]:
            if not e.get("discovery"):
                continue
            key = collection_key(e["discovery"])
            if key in book["items"]:
                continue
            book["items"][key] = {"count": 1, "first_seed": st["seed"], "first_date": walk_date}
            added.append(key)
        if not book.get("aptitude"):
            book["aptitude"] = st["setup"].get("aptitude")
        imported.append(st["seed"])
        save_collection(args.file, book)
        summary = collection_summary(book, book.get("aptitude"))
        out({"ok": True, "added": added, "seed": st["seed"], "date": walk_date, **summary})
        return
    book = load_collection(args.file)
    items = [{"item": k, "count": v.get("count", 1),
              "first_date": v.get("first_date"), "first_seed": v.get("first_seed")}
             for k, v in sorted(book["items"].items(), key=lambda kv: (kv[1].get("first_date") or "", kv[0]))]
    summary = collection_summary(book, book.get("aptitude"))
    out({"ok": True, "agent_id": book.get("agent_id"), **summary, "items": items})


# 5軸診断: 散歩のジレンマ10問に A/B で答えると、その子の歩き方の配分（合計15点）が決まる。
# 各軸は最大で4問までしか担当しないので、配分は必ず「全軸1点＋回答の10点＝各1〜5点・合計15点」に収まる。
# 答えるのはプレイヤー自身（マスターではない）。性格診断ではなく「散歩の癖」の診断。
DIAGNOSE_QUESTIONS = [
    {"q": "朝の散歩。知らない路地と、評判のカフェが並んでいたら？", "a": ("路地に入ってみる", "curiosity"), "b": ("カフェで一息つく", "chill")},
    {"q": "焼き立ての匂いがしてきた。お店には列ができていたら？", "a": ("列に並んで焼き立てを待つ", "foodie"), "b": ("匂いだけ楽しんで先へ進む", "adventure")},
    {"q": "看板猫が段ボールで丸くなって昼寝している。", "a": ("近づいて挨拶する", "friendly"), "b": ("遠くから眺めて休む", "chill")},
    {"q": "路地の壁に、小さい絵が描かれているのを見つけた。", "a": ("しゃがんでじっくり見る", "curiosity"), "b": ("描いた人を探して進む", "adventure")},
    {"q": "人気の屋台に長い列ができている。", "a": ("並んで一番人気を買う", "foodie"), "b": ("列の人と話しながら待つ", "friendly")},
    {"q": "夕方の公園に着いた。", "a": ("ベンチでのんびりする", "chill"), "b": ("一番高い場所まで登る", "adventure")},
    {"q": "知らない花が咲いている。", "a": ("名前を調べて覚える", "curiosity"), "b": ("近くの人に聞いてみる", "friendly")},
    {"q": "お腹が空いてきた。", "a": ("匂いのする方へ向かう", "foodie"), "b": ("景色のいい場所で休む", "chill")},
    {"q": "落とし物を見つけた。", "a": ("届け先へ持って行く", "friendly"), "b": ("手がかりをよく観察する", "curiosity")},
    {"q": "帰り道、遠回りもできそう。", "a": ("遠回りして知らない道を行く", "adventure"), "b": ("近道でおやつを買って帰る", "foodie")},
]

AXIS_LABELS = {"curiosity": "好奇心", "chill": "のんびり", "foodie": "食いしん坊",
               "friendly": "人なつっこさ", "adventure": "冒険心"}


def cmd_diagnose(args):
    if not getattr(args, "answers", None):
        out({"ok": True,
             "questions": [{"n": i + 1, "question": q["q"], "A": q["a"][0], "B": q["b"][0]}
                           for i, q in enumerate(DIAGNOSE_QUESTIONS)],
             "how": "10問とも、自分の気持ちで A か B を選んでください（マスターに相談しないのが約束です）。"
                    "選んだら --answers に10文字で渡してください（例: ABABBABAAB）。"})
    ans = args.answers.strip().upper()
    if len(ans) != 10 or any(c not in "AB" for c in ans):
        out({"ok": False, "error": "answers must be 10 chars of A/B"}, 1)
    apt = {a: 1 for a in AXES}
    for c, q in zip(ans, DIAGNOSE_QUESTIONS):
        apt[q["a"][1] if c == "A" else q["b"][1]] += 1
    top = max(AXES, key=lambda a: apt[a])
    out({"ok": True, "aptitude": apt, "style_axis_labels": AXIS_LABELS,
         "top_axis": top, "top_axis_label": AXIS_LABELS[top],
         "note": "この配分を setup.json の aptitude にそのまま使えます（合計15点・各1〜5点）。"})


def main():
    ap = argparse.ArgumentParser(prog="osanpo")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("--seed", required=True); p.add_argument("--setup", required=True)
    p.add_argument("--theme-file", required=True); p.add_argument("--run-dir", required=True); p.add_argument("--json", action="store_true")
    p.add_argument("--collection", default=None, help="発見図鑑ファイルのパス（任意。渡すと finish で自動登録される）")
    p.add_argument("--season", default=None, help="季節の明示指定（winter / none）。省略時は日付から自動判定")
    p = sub.add_parser("status"); p.add_argument("--run-dir", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("choose"); p.add_argument("choice"); p.add_argument("--reason", default="")
    p.add_argument("--run-dir", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("comment"); p.add_argument("--text", required=True)
    p.add_argument("--run-dir", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("finish"); p.add_argument("--epilogue", default="")
    p.add_argument("--run-dir", required=True); p.add_argument("--json", action="store_true")
    p = sub.add_parser("collection"); p.add_argument("--file", required=True); p.add_argument("--json", action="store_true")
    p.add_argument("--add-run", default=None, help="図鑑ができる前の散歩を、記録フォルダから後付け登録する")
    p = sub.add_parser("diagnose"); p.add_argument("--answers", default=None, help="10問への回答（A/Bの10文字）")
    p.add_argument("--json", action="store_true")
    args = ap.parse_args()
    {"new": cmd_new, "status": cmd_status, "choose": cmd_choose,
     "comment": cmd_comment, "finish": cmd_finish, "collection": cmd_collection,
     "diagnose": cmd_diagnose}[args.cmd](args)


if __name__ == "__main__":
    main()
