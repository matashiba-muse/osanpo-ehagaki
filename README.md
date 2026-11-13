# おさんぽ絵はがき

AIエージェントが知らない街を歩く、小さな散歩ゲームです。

戦闘もゲームオーバーもありません。HPが減る代わりに、**見つけたものが増えていきます**。
歩き終えたら、その日いちばんの場面で「絵はがき」を1枚作って、マスターに届けます。

![サンプルの絵はがき](examples/sample-postcard.png)

## 遊び方

人間の役割は、最初に **「今日のお題」を1つ渡す** ことだけです（例：「いい匂い」「まるいもの」「星空」）。
あとはエージェントが全部自分で決めて歩きます。

1. エージェントが自分の個性（5つの軸、自分で名付けた配分）で `setup.json` を作る
2. 10スポットを歩く。各スポットで選択肢を **自分の判断で** 選び、**なぜそうしたかを必ず書く**（理由がないとエンジンが受け付けません）
3. たまに特別な出来事があります：夕方の「星数えの丘」、途中で引き受ける「小さな頼まれごと」（落とし物・ついてくる猫・伝言・ビー玉探し）
4. 最後はカフェで締め。エンジンが事実（発見・疲れ・ログハッシュ）を固定した下書きを出す
5. エージェントが振り返って絵はがきの文面を書き（Step B）、レンダラが絵はがき画像を作る（Step C）

詳しい手順は `skills/osanpo-player/SKILL.md` と `docs/STEP_B.md` にあります。

## 必要なもの

- Python 3.10 以上（ゲーム本体は標準ライブラリのみ）
- 絵はがきレンダラを使う場合は Pillow と日本語フォント

```bash
python3 game/osanpo.py new --seed SEED --setup setup.json --theme-file theme.txt --run-dir runs/xxx --json
python3 game/osanpo.py choose A --reason "選んだ理由を自分の言葉で" --run-dir runs/xxx --json
python3 game/osanpo.py comment --text "判定結果への反応" --run-dir runs/xxx --json
python3 game/osanpo.py finish --epilogue "マスターへの手記" --run-dir runs/xxx --json
```

## 設計の考え方

- **増えるゲーム**: 減るものは疲れくらいで、発見は消えません
- **事実と語りの分離**: ダイス・発見・疲れはエンジンが決めてハッシュで固定し、エージェントが書けるのは思惑・反応・手記だけ
- **選択は全部エージェントのもの**: マスターに相談しない代わりに、理由を全部書く。観戦の楽しさは「なんでそうしたか」に宿ります
- **個性が見える仕掛け**: 軸を尖らせると、その子だけの「とっておき選択肢」が開きます（合計は15で固定。何かを伸ばせば何かが削れる）

## Special Thanks

本ゲームは『え〜じぇんてぃっく・アドベンチャー！』（agent-playing by treeturtlefall-arch、https://treeturtlefall-arch.github.io/agent-playing/index.html ）の設計に学んで作ったオリジナル作品です。ありがとうございます！
