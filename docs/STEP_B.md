# Step B 手順書：絵はがき文面（postcard.json）の作り方

Step A（ゲームCLI）の finish が出した `walk_draft.json` を読み、プレイヤー本人が自分の言葉で `postcard.json` を書く工程。agent-playing の Step B と同じ規律で運用する。

## 1. 読み込むもの

- 対象ランの `walk_draft.json`（事実の正本）
- 対象ランの `walk.md`（自分の思惑・反応・手記の原文）
- 対象ランの `setup.json` の `private_owner_names`（検疫用。この工程でも再確認する）

## 2. postcard.json の形式

```json
{
  "schema_version": "0.2",
  "agent": {"name": "...", "id": "..."},
  "challenge": {"seed": "...", "theme": "..."},
  "postcard_spot": {"floor": 0, "event_id": "...", "event_title": "...", "rank": "success"},
  "discoveries": [{"floor": 0, "event_id": "...", "item": "...", "theme_hit": false, "rare": false}],
  "metrics": {"discoveries": 0, "theme_discoveries": 0, "final_fatigue": 0},
  "verification": {"log_hash": "...", "action_log_ref": "logs/...", "replayable": true},
  "postcard_text": {
    "headline": "見出し（自分で書く）",
    "body": "絵はがき本文（自分で書く）",
    "to_master": "マスターへの一言（自分で書く）",
    "scene_caption": "絵はがき場面の説明（自分で書く）"
  },
  "illustration_brief": {"scene": "Step C で描く場面イラストの指示"},
  "credit": {"production": "制作: 自分の名前"}（任意。自分の制作名だけを書く。Special Thanks は入れない——それは作者自身の絵はがきのためのもの）
}
```

## 3. 書き換えてよいもの／いけないもの

- **コピーしてそのまま使う（書き換え禁止）**: agent / challenge / postcard_spot / discoveries / metrics / verification。これらはエンジンの事実で、レンダラが walk_draft.json と照合し、発見リスト・場面・ハッシュが1つでも違ったら描画を中止する。
- **自分で書く**: postcard_text（headline / body / to_master / scene_caption）と illustration_brief だけ。walk.md の自分の言葉を土台に、その日の散歩らしさが出る文面にする。絵はがき場面（postcard_spot）の情景に触れること。
- **書いてはいけないもの**: オーナーの私的な名前（`private_owner_names` の語）。宛名が必要ならロールプレイ上の呼称（例：マスター）を使う。

## 4. 検疫（プライバシー二重チェック）

1. Step B の書き手が、 postcard.json を保存する前に private_owner_names で全文検索する（1回目）。
2. レンダラ（Step C）が描画直前に同じ検索を機械的に行い、混入していたら描画を中止する（2回目）。

どちらかで引っかかったら、その語を呼称に置き換えてからやり直す。検疫リスト自体は postcard.json に書き込まない。
