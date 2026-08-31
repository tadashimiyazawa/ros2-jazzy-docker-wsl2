# セットアップマニュアル — 何もない Windows PC から ROS 2 開発環境まで

Windows PC に WSL2 を入れるところから、この ROS 2 Jazzy 環境が動いてロボットが
シミュレータの中を走り出すところまでの手順書です。

**対象** — Linux も Docker も ROS も初めて、という前提で書いています。
コマンドは上から順にコピーして貼るだけで進みます。

**所要時間** — 待ち時間込みで **1〜2 時間**。うち 15〜30 分は
ダウンロードを眺めているだけの時間です（回線速度によります）。

**終わったときの状態**

- Windows の中に Ubuntu 24.04 が動いている（Windows は変更されない）
- その中の Docker コンテナに ROS 2 Jazzy が入っている（Ubuntu も汚れない）
- `./demo.sh` と打つとロボットが自律走行し、RViz2 の画面に映る
- （任意）Claude Code が入っていて、詰まったときに相談できる

**この文書の読み方** — 各ステップに「なぜこれをやるのか」を短く添えています。
急ぐ場合はコマンド部分だけ拾ってください。
`> ` で始まる引用は、つまずきやすい点の注意書きです。

用語が分からなくなったら [付録 A の用語集](#付録-a-用語集) を見てください。
作った後の「使い方」は [README.md](README.md)、
「なぜそういう作りなのか」は [PRACTICES.md](PRACTICES.md) にあります。

---

## 目次

- [ステップ 0. 前提の確認](#ステップ-0-前提の確認)
- [ステップ 1. WSL2 と Ubuntu を入れる](#ステップ-1-wsl2-と-ubuntu-を入れる)
- [ステップ 2. Ubuntu の初期設定](#ステップ-2-ubuntu-の初期設定)
- [ステップ 3. Docker を入れる](#ステップ-3-docker-を入れる)
- [ステップ 4. Claude Code を入れる](#ステップ-4-claude-code-を入れる)
- [ステップ 5. GUI（画面表示）が使えるか確認する](#ステップ-5-gui画面表示が使えるか確認する)
- [ステップ 6. プロジェクトのファイルを置く](#ステップ-6-プロジェクトのファイルを置く)
- [ステップ 7. 初回ビルドとコンテナ起動](#ステップ-7-初回ビルドとコンテナ起動)
- [ステップ 8. 動作確認](#ステップ-8-動作確認)
- [ステップ 9. 毎日の使い方](#ステップ-9-毎日の使い方)
- [トラブルシューティング](#トラブルシューティング)
- [付録 A. 用語集](#付録-a-用語集)
- [付録 B. ゼロから自分で組み立てる場合の順番](#付録-b-ゼロから自分で組み立てる場合の順番)

---

## ステップ 0. 前提の確認

### 0.1 必要なもの

| 項目 | 必要な条件 | 確認方法 |
|---|---|---|
| OS | Windows 11、または Windows 10 バージョン 21H2 以上 | `Win + R` → `winver` |
| メモリ | 8GB 以上（16GB 推奨） | タスクマネージャー →「パフォーマンス」 |
| 空きディスク | **30GB 以上**（ROS のイメージだけで 7GB 近く使います） | エクスプローラーで C: を右クリック |
| CPU の仮想化支援 | 有効 | タスクマネージャー →「パフォーマンス」→「CPU」→「仮想化: 有効」 |
| ネットワーク | 数 GB のダウンロードができること | — |

> **仮想化が「無効」だった場合** — PC の BIOS/UEFI 設定で有効にする必要があります。
> 起動時に F2 や Del を押して設定画面に入り、`Intel VT-x` / `AMD-V` / `SVM Mode`
> といった項目を Enabled にしてください。ここは機種ごとに場所が違うので、
> 「(機種名) BIOS 仮想化 有効」で検索するのが早いです。

> **会社の PC の場合** — 管理者権限が必要です。また、セキュリティソフトが WSL を
> ブロックする設定になっていることがあります。うまくいかない場合は情報システム部門へ。

### 0.2 これから何をするのか（全体像）

```
Windows
 └─ WSL2                     ← ステップ 1（Windows の中で Linux を動かす仕組み）
     └─ Ubuntu 24.04         ← ステップ 1〜2（Linux 本体）
         ├─ Claude Code      ← ステップ 4（作業を手伝う AI。任意）
         └─ Docker           ← ステップ 3（アプリを箱に隔離して動かす仕組み）
             └─ コンテナ      ← ステップ 7（この箱の中に ROS 2 が入る）
                 └─ ROS 2 Jazzy + Gazebo + RViz2
```

**なぜ何重にもするのか** — ROS 2 は数百個のパッケージを OS 全体に入れるため、
直接インストールすると環境が壊れたときに戻せません。
一番内側の箱（コンテナ）に閉じ込めておけば、壊れても箱を捨てて作り直すだけで済みます。
Windows も Ubuntu も汚れません。

---

## ステップ 1. WSL2 と Ubuntu を入れる

### 1.1 PowerShell を管理者として開く

スタートボタンを**右クリック** →「ターミナル (管理者)」または
「Windows PowerShell (管理者)」を選びます。
「このアプリがデバイスに変更を加えることを許可しますか?」には「はい」。

### 1.2 WSL と Ubuntu 24.04 をインストールする

```powershell
wsl --install -d Ubuntu-24.04
```

これ 1 行で、WSL2 の有効化・カーネルの導入・Ubuntu 24.04 の取得まで全部やってくれます。
数分かかります。

> **`wsl` が見つからないと言われたら** — Windows が古い可能性があります。
> Windows Update を最後まで当ててからやり直してください。

> **すでに WSL を使ったことがある PC の場合** — 先に `wsl --update` で
> WSL 本体を最新にしてから上のコマンドを実行してください。
> 古い WSL には GUI 機能（WSLg）が入っていません。

終わったら **Windows を再起動**します。

### 1.3 Ubuntu の初回起動とユーザー作成

再起動後、スタートメニューから「Ubuntu 24.04」を起動します
（自動で黒い画面が開くこともあります）。

初回だけ数分かかったあと、こう聞かれます:

```
Enter new UNIX username:
```

**ここで作るユーザーが、以降すべての作業の主になります。**

- ユーザー名は**半角英小文字のみ**（記号・大文字・日本語は避ける）
- 続いてパスワードを 2 回聞かれます。**入力しても画面に何も表示されませんが、
  ちゃんと入っています**（Linux ではこれが普通です）。忘れないものにしてください

> **なぜ重要か** — ここで最初に作られたユーザーには内部的に `1000` という
> 番号（UID）が割り当てられます。この環境は「コンテナの中のユーザーも 1000」に
> 揃えることで、コンテナが作ったファイルを Windows 側からも編集できるようにしています。
> 番号がずれると、あとで「自分が作ったファイルなのに保存できない」という状態になります。
> 詳しくは [PRACTICES.md の 1.3](PRACTICES.md#13-ホストとコンテナで-uid-を揃える)。

作成できたか確認します。**`uid=1000` になっていれば正解**です:

```bash
id
```

```
uid=1000(あなたの名前) gid=1000(あなたの名前) groups=1000(...),27(sudo),...
```

### 1.4 WSL2 で動いているか確認する

PowerShell（管理者でなくてよい）で:

```powershell
wsl -l -v
```

```
  NAME            STATE           VERSION
* Ubuntu-24.04    Running         2
```

**VERSION が `2` であること**を確認してください。`1` になっていたら:

```powershell
wsl --set-version Ubuntu-24.04 2
wsl --set-default-version 2
```

> WSL1 では Docker も GUI も動きません。ここは必ず 2 にしてください。

### 1.5 （任意）WSL が使うメモリの上限を決める

WSL2 は既定で Windows の物理メモリの半分まで使います。
足りない／使いすぎる場合は、Windows 側のユーザーフォルダに `.wslconfig` を作ります。

PowerShell で:

```powershell
notepad "$env:USERPROFILE\.wslconfig"
```

「新しく作りますか」に「はい」と答え、次を貼って保存:

```ini
[wsl2]
memory=12GB
processors=8
swap=4GB
```

反映するには `wsl --shutdown` を実行してから Ubuntu を開き直します。

> Gazebo（ロボットシミュレータ）は重いので、**メモリは 8GB 以上**割り当ててください。

---

## ステップ 2. Ubuntu の初期設定

ここからは **Ubuntu の画面**（黒いターミナル）で作業します。

### 2.1 パッケージを最新にする

```bash
sudo apt update && sudo apt upgrade -y
```

`sudo` は「管理者として実行する」という意味です。最初にパスワードを聞かれます
（ステップ 1.3 で決めたもの。**入力しても表示されません**）。

数分かかります。

### 2.2 systemd が有効か確認する

```bash
cat /etc/wsl.conf
```

こう表示されれば OK です:

```
[boot]
systemd=true
```

**ファイルが無い、または `systemd=true` が無い場合**は追記します:

```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true
EOF
```

そのあと PowerShell で一度 WSL を落とし、Ubuntu を開き直します:

```powershell
wsl --shutdown
```

> **なぜ必要か** — Docker はバックグラウンドで常駐するサービス（デーモン）です。
> systemd はそれを自動起動・管理する仕組みで、これが無いと
> 毎回手動で Docker を起動する羽目になります。

### 2.3 基本的な道具を入れる

```bash
sudo apt install -y curl git nano
```

- `curl` — ネットからファイルを取ってくる（ステップ 3・4 で使う）
- `git` — ソースコードの管理
- `nano` — 初心者向けのテキストエディタ（保存は `Ctrl+O` → `Enter`、終了は `Ctrl+X`）

---

## ステップ 3. Docker を入れる

Docker は「アプリと、それが必要とする OS 環境ごと箱に詰めて動かす」仕組みです。
ROS 2 一式をこの箱に入れます。

> **Docker Desktop（Windows 版）は不要です。** Ubuntu の中に直接入れます。
> Docker Desktop を使う方法もありますが、商用利用に条件があり、
> GUI まわりの設定もこの手順書とは変わります。

### 3.1 Docker 公式リポジトリを登録する

以下を**まとめてコピーして貼り付け**ます（1 行ずつでも構いません）:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
```

> Ubuntu 標準の `docker.io` パッケージでも動きますが、バージョンが古いことがあります。
> 公式リポジトリを使うのが確実です。

### 3.2 Docker 本体をインストールする

```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

`docker-compose-plugin` は、この環境で使う `docker compose` コマンドです。**必須**です。

### 3.3 sudo なしで docker を使えるようにする

```bash
sudo usermod -aG docker $USER
```

**この設定を反映するには、いったんログインし直す必要があります。**
PowerShell で:

```powershell
wsl --shutdown
```

そして Ubuntu を開き直してください。

### 3.4 動作確認

```bash
docker run --rm hello-world
```

`Hello from Docker!` と表示されれば成功です。

```bash
docker compose version
```

`Docker Compose version v2...` のようにバージョンが出れば OK。

> **`permission denied` と言われたら** — 3.3 の再起動ができていません。
> `wsl --shutdown` をもう一度実行してください。
> **`Cannot connect to the Docker daemon` と言われたら** — サービスが起動していません。
> `sudo systemctl start docker` を実行し、`sudo systemctl enable docker` で自動起動にします。

<details>
<summary>参考: この環境を作った PC は snap 版の Docker を使っています（クリックで展開）</summary>

元の PC では `sudo snap install docker` で入れた snap 版が動いています。
snap 版には**コンテナに `/usr` 以下をマウントできない**という制約があり、
この環境の `Dockerfile` / `compose.yaml` にはその回避策が入っています
（[PRACTICES.md の 3 章](PRACTICES.md#3-wsl2--wslg-固有の壁)）。

回避策は公式版 Docker でもそのまま無害に動くので、**このマニュアル通り
公式版を入れて問題ありません**。あえて snap 版に合わせる場合は:

```bash
sudo snap install docker
sudo addgroup --system docker
sudo adduser $USER docker
newgrp docker
sudo snap disable docker && sudo snap enable docker
```

なお snap 版では、プロジェクトをホームディレクトリの下
（`~/workspace/...`）に置くようにしてください。

</details>

---

## ステップ 4. Claude Code を入れる

**Claude Code** は、ターミナルの中で動く AI コーディング支援ツールです。
ファイルを読み書きし、コマンドを実行し、エラーの原因を調べてくれます。

**この環境自体、Claude Code と対話しながら組み立てたものです。**
`Dockerfile` や `compose.yaml` に入っている回避策
（[PRACTICES.md の 3 章](PRACTICES.md#3-wsl2--wslg-固有の壁)）は、
エラーが出るたびに原因を調べ、直し、理由をコメントに残す、を繰り返した結果です。

> **必須ではありません。** 手順書通りに進めるだけならスキップして
> [ステップ 5](#ステップ-5-gui画面表示が使えるか確認する) へ進んで構いません。
> ただし、この先で環境固有のエラーに当たったとき
> （そして初めての環境構築では必ず当たります）、
> エラー文をそのまま貼って聞ける相手がいるのは大きな違いになります。

### 4.1 事前に必要なもの

- **Claude の契約** — Claude Pro / Max などのサブスクリプション、
  または Anthropic Console の API クレジット。どちらか一方があれば使えます
- ネットワーク接続

### 4.2 インストールする

**Ubuntu のターミナル**で（コンテナの中ではありません）:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

数十秒で終わります。`~/.local/share/claude/` に本体が入り、
`~/.local/bin/claude` から呼べるようになります。

> **Node.js は不要です。** 単体で動くバイナリが入ります。
> （npm を使う方法もあります: `npm install -g @anthropic-ai/claude-code`。
> その場合は Node.js 18 以上が必要です。どちらか一方で構いません）

インストール後、**PATH を反映するためにターミナルを開き直します**。
または:

```bash
source ~/.bashrc
```

確認:

```bash
claude --version
```

```
2.1.x (Claude Code)
```

> **`claude: command not found` と出たら** — PATH が通っていません。
> 次を実行してターミナルを開き直してください:
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
> ```

### 4.3 初回起動とログイン

作業したいフォルダに移動してから起動します:

```bash
mkdir -p ~/workspace
cd ~/workspace
claude
```

初回だけ次を聞かれます:

1. **テーマの選択** — 見た目の好みです。矢印キーで選んで `Enter`
2. **ログイン方法** — サブスクリプションなら「Claude account」、
   API キーを使うなら「Anthropic Console」
3. **ブラウザが開く** — WSL から Windows の既定ブラウザが開きます。
   ログインして、表示された認証コードをターミナルに貼り付けます

> **ブラウザが開かない場合** — ターミナルに URL が表示されているので、
> それをコピーして Windows のブラウザに手で貼り付けてください。
> WSL から Windows のブラウザを開けないことが稀にあります。

4. **フォルダを信頼するか** — 「Yes, I trust this folder」を選びます。
   Claude Code はそのフォルダの中のファイルしか触りません

ログインが済むと、こう表示されて入力待ちになります:

```
╭───────────────────────────────────────────╮
│ ✻ Welcome to Claude Code                  │
╰───────────────────────────────────────────╯

> 
```

日本語でそのまま話しかけて構いません。

### 4.4 基本の操作

| したいこと | 操作 |
|---|---|
| 起動する | 作業フォルダで `claude` |
| 終了する | `/exit` と入力、または `Ctrl+D` |
| 実行中の処理を止める | `Ctrl+C` |
| 前回の続きから始める | `claude --continue` |
| 使えるコマンドを見る | `/help` |
| インストールの状態を調べる | `claude doctor` |

**改行を入れたいとき**（複数行の指示を書くとき）は `Shift+Enter`、
または行末に `\` を置いて `Enter`。
`Enter` だけだとその場で送信されます。

### 4.5 どこで起動するか — Ubuntu 側であって、コンテナの中ではない

```
Windows
 └─ Ubuntu 24.04      ← ここで claude を起動する
     ├─ Claude Code
     └─ Docker
         └─ コンテナ   ← ROS 2 はこの中。中には入れない
```

**理由** — この環境は「ファイルの編集はホスト側、ビルドと実行はコンテナ内」
という分担になっています（[PRACTICES.md の 1.2](PRACTICES.md#12-ソースはホストビルドと実行はコンテナ)）。
Claude Code は編集する側なので Ubuntu 側に置きます。
コンテナ内でコマンドを試したいときは、Claude Code に
`docker compose exec ros bash -lc '...'` を実行させれば届きます。

### 4.6 権限の確認について

Claude Code は、ファイルを書き換えるときやコマンドを実行するときに
毎回確認を出します。**内容を読んでから許可してください**
（特に `rm` や `docker compose down -v` のように消す操作）。

同じ確認が繰り返されて煩わしくなったら、
プロジェクトごとの許可リストに書けます。この環境には例が入っています:

```bash
cat ~/workspace/ros/.claude/settings.local.json
```

```json
{
  "permissions": {
    "allow": [
      "Bash(docker image *)"
    ]
  }
}
```

「イメージの一覧を見るだけ」のような**安全な読み取り操作だけ**を許可し、
消す操作は手動確認に残す、という線引きにしてあります
（[PRACTICES.md の 8.4](PRACTICES.md#84-権限は最小で明示する)）。

### 4.7 この環境を作るときに実際に効いた使い方

初心者が環境構築で使う場合、次のような聞き方が効きます。

**エラーをそのまま貼る** — 要約せず、出力を全部貼るのが一番速いです。

```
> docker compose up したらこのエラーが出ました。原因と直し方を教えてください。
  (エラー出力をそのまま貼り付け)
```

**「なぜ」を聞く** — 動いた後に理由を聞いておくと、次に応用が効きます。

```
> compose.yaml の shm_size は何のために必要なんですか？
```

**理由をコメントとして残させる** — これが一番重要です。

```
> 今の回避策が必要な理由を、compose.yaml のコメントとして書き足してください。
```

> **なぜ重要か** — 回避策は、見た目には「不自然なコード」です。
> 理由が書かれていないと、後から自分でも AI でも「これは要らない」と判断して消し、
> 同じ問題を踏み直します（[PRACTICES.md の 8.1](PRACTICES.md#81-なぜをコードのコメントとして残す)）。

**確認できたことを記録させる** — 「動いた」と「確かめた」は違います。

```
> ここまでで実際に動作確認できた項目を README に追記してください。
```

### 4.8 注意しておくこと

- **生成されたものは、確認するまで動く保証がありません。**
  必ず自分で実行して確かめてください。この手順書の各ステップに
  動作確認が入っているのはそのためです
- **消す操作は自分で判断する。** `docker compose down -v` や
  `wsl --unregister` は取り返しがつきません
- **秘密情報を貼らない。** パスワードや API キーはそのまま貼らないこと
- **更新** — 通常は自動で更新されます。手動で上げたいときは
  `claude install stable`

---

## ステップ 5. GUI（画面表示）が使えるか確認する

WSL2 には **WSLg** という仕組みが入っていて、Linux のウィンドウが
そのまま Windows のデスクトップに出ます。追加のソフト（X サーバ）は要りません。
RViz2 や Gazebo の画面はこれで表示されます。

先に動くことを確かめておきます:

```bash
sudo apt install -y x11-apps
xeyes
```

**目玉がマウスを追いかけるウィンドウ**が Windows のデスクトップに出れば成功です。
`Ctrl+C` で閉じます。

> **何も出ない場合** — WSL が古い可能性があります。PowerShell（管理者）で
> `wsl --update` してから `wsl --shutdown`、そしてやり直してください。

### GPU について（読み飛ばして構いません）

この種の環境では、3D 描画が GPU ではなく CPU で処理されることがあります。
元の PC もそうで、Gazebo は実時間の 7 割程度の速さで動いています。
学習用途では十分ですが、「思ったより遅い」と感じたらこれが理由です。
設定は済ませてあるので、環境が対応すれば自動的に速くなります
（[PRACTICES.md の 3.4](PRACTICES.md#34-動く経路と速い経路を分けて記録する)）。

---

## ステップ 6. プロジェクトのファイルを置く

### 6.1 置き場所を作る

```bash
mkdir -p ~/workspace
cd ~/workspace
```

> **重要: `/mnt/c/...`（Windows 側のフォルダ）には置かないでください。**
> Windows と Linux のファイルシステムをまたぐと読み書きが極端に遅くなり、
> ファイルの権限も正しく扱えません。必ず Linux 側のホーム（`~/`）の下に置きます。

### 6.2 ファイル一式を取得する

**方法 A: Git リポジトリから取ってくる（推奨）**

```bash
cd ~/workspace
git clone <リポジトリのURL> ros
cd ros
```

**方法 B: 別の PC から手でコピーする**

必要なのは次のファイルだけです。生成物（`ws/build`・`ws/install`・`ws/log`・
`.wslgpu` の中身）はコピー不要です。

```
ros/
├── Dockerfile          コンテナの中身の定義
├── compose.yaml        起動時の設定（GUI・ネットワーク・共有フォルダ）
├── run.sh              コンテナに入るためのスクリプト
├── demo.sh             デモを一発で動かすスクリプト
├── README.md           使い方
├── PRACTICES.md        設計の意図
├── .gitignore
└── ws/                 ROS ワークスペース（Windows 側からも編集できる場所）
    ├── .gitignore
    ├── launch/
    │   └── tb3_headless.launch.py    Gazebo を画面なしで起動する定義
    └── scripts/
        ├── robot.py        ロボットを動かす操作ツール
        ├── sim_speed.py    シミュレータの速度を測る
        └── draw_square.py  turtlesim 用の練習コード
```

> **Windows のメモ帳などでファイルを作った場合の注意** — 改行コードが
> Windows 形式（CRLF）になっていると、`run.sh` が
> `bad interpreter: /usr/bin/env bash^M` というエラーで動きません。
> その場合は `sudo apt install -y dos2unix && dos2unix run.sh demo.sh` で直せます。

### 6.3 スクリプトに実行権限をつける

```bash
cd ~/workspace/ros
chmod +x run.sh demo.sh
```

### 6.4 GPU ライブラリ用の空フォルダを用意する

```bash
mkdir -p .wslgpu && touch .wslgpu/.keep
```

`Dockerfile` がこのフォルダを参照するため、空でも存在している必要があります。
中身は `run.sh` が実行時に自動で用意します。

### 6.5 各ファイルが何をしているか（概要）

中身を理解しなくても動きますが、あとで自分用に変えるときのために。

| ファイル | 役割 | 変えたくなったら |
|---|---|---|
| `Dockerfile` | 箱の中身のレシピ。ベースの ROS イメージに、開発ツールとシミュレータを追加している | パッケージを追加したいとき（`apt install` の行に足す） |
| `compose.yaml` | 箱の動かし方。画面・ネットワーク・共有フォルダ・メモリの設定 | USB 機器を繋ぐ、通信範囲を変える |
| `run.sh` | 箱に入るためのコマンド。無ければ作り、止まっていれば起動して、シェルを開く | 基本そのまま |
| `demo.sh` | シミュレータ起動 → 可視化 → 自律走行 を自動で通す | デモの秒数を変える |
| `ws/` | **自分のコードを置く場所。** Windows 側からも Linux 側からも見える | ここで開発する |

詳しい理由は [PRACTICES.md](PRACTICES.md) にあります。

---

## ステップ 7. 初回ビルドとコンテナ起動

```bash
cd ~/workspace/ros
./run.sh
```

**初回は 15〜30 分かかります。**
6.35GB のベースイメージのダウンロードと、その上への追加インストールが走るためです。
コーヒーを淹れに行ってください。

進行中はこんな表示が延々と流れます（正常です）:

```
==> Image not found, building (first run takes a few minutes)...
[+] Building 892.3s (14/14) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 3.50kB
 ...
==> Starting ros2-jazzy...
```

終わると、**プロンプトの表示が変わります**:

```
rosdev@ros2-jazzy:/ws$
```

`rosdev@ros2-jazzy` になっていれば、**あなたは今コンテナの中にいます**。
ここから先の `ros2` コマンドはすべてこの中で実行します。

> **元に戻る（コンテナから出る）には** `exit` と打ちます。
> コンテナは動いたままなので、`./run.sh` でまた入れます。

> **失敗した場合** — 多くはネットワーク断かディスク不足です。
> `df -h /` で空きを確認し、`./run.sh` をもう一度実行してください。
> 途中まで進んだ分はキャッシュされているので、やり直しは速く済みます。

---

## ステップ 8. 動作確認

### 8.1 ROS 2 が入っているか

コンテナの中（`rosdev@ros2-jazzy:/ws$`）で:

```bash
ros2 --version
```

```
ros2 cli version: 0.32.x
```

### 8.2 ノード同士の通信（ROS の基本）

ROS では、小さなプログラム（**ノード**）同士が
**トピック**という名前付きの通信路でメッセージをやり取りします。
送る側と受け取る側を動かしてみます。

**ターミナル 1**（今のコンテナの中）:

```bash
ros2 run demo_nodes_cpp talker
```

```
[INFO] [talker]: Publishing: 'Hello World: 1'
[INFO] [talker]: Publishing: 'Hello World: 2'
```

**ターミナル 2** — Ubuntu の窓を**もう 1 つ**開きます
（スタートメニューから「Ubuntu 24.04」をもう一度起動）:

```bash
cd ~/workspace/ros
./run.sh
ros2 run demo_nodes_cpp listener
```

```
[INFO] [listener]: I heard: [Hello World: 5]
```

**送った番号と受け取った番号が対応していれば成功です。**
両方 `Ctrl+C` で止めます。

> `./run.sh` は何回実行しても**同じコンテナに繋がります**。
> ROS の作業はターミナルを 3〜4 枚開くのが普通なので、この形にしてあります。

### 8.3 GUI（RViz2）

```bash
rviz2
```

Windows のデスクトップに RViz2（ROS の可視化ツール）のウィンドウが開けば成功です。
起動に 10〜20 秒かかることがあります。`Ctrl+C` で閉じます。

### 8.4 ロボットを走らせる（デモ）

いったんコンテナを出ます（`exit`）。Ubuntu 側で:

```bash
cd ~/workspace/ros
./demo.sh
```

順に次が起きます:

1. Gazebo（物理シミュレータ）が画面なしで起動する（約 45 秒）
2. RViz2 が開き、ロボットと LiDAR（レーザー距離計）の点が表示される
3. ロボットが 120 秒間、障害物を避けながら自律走行する

ターミナルにはこう流れます:

```
==> Starting Gazebo (this takes ~45s)...
    waiting for the robot to come up... ok
==> Starting RViz2...
==> Robot state:
pose      x=-2.000 m  y=-0.500 m  yaw=+0.0 deg
cmd type  Twist
front     3.021 m
==> Wandering for 120s (Ctrl-C to stop early)...
x=-1.00 y=-0.50  moved 1.00 m
x=-0.35 y=-0.50  moved 0.65 m  blocked
  turning +90 deg toward open space
```

**RViz2 の画面でロボットが動いていれば、環境構築は完了です。**

止めるとき:

```bash
./demo.sh --stop
```

Gazebo の画面も見たい場合は `./demo.sh --gui`（15% ほど遅くなります）。

### 8.5 自分でロボットを動かしてみる

デモを止めていない状態で、別のターミナルから:

```bash
cd ~/workspace/ros
./run.sh
python3 /ws/scripts/robot.py status        # 今どこにいるか、前方に何があるか
python3 /ws/scripts/robot.py forward 1.0   # 1m 前進
python3 /ws/scripts/robot.py turn -90      # 右に 90 度回る
python3 /ws/scripts/robot.py square 1.0    # 一辺 1m の四角を描く
```

壁に向かって `forward 10` と命令しても、**手前で必ず止まります**
（レーザーを見て安全停止するようになっています）。安心して試してください。

---

## ステップ 9. 毎日の使い方

### 起動と終了

```bash
cd ~/workspace/ros
./run.sh                 # 入る（2 回目以降は数秒）
exit                     # 出る（コンテナは動いたまま）

docker compose down      # コンテナを止める。ws/ の中身は消えない
docker compose down -v   # キャッシュごと消す
```

PC の電源を切れば全部止まります。次に `./run.sh` すればまた動きます。

### コードを書く（VS Code を使う場合）

Windows 側に [Visual Studio Code](https://code.visualstudio.com/) を入れ、
拡張機能 **WSL** をインストールします。そのうえで Ubuntu のターミナルから:

```bash
cd ~/workspace/ros
code .
```

Windows の VS Code が開き、Linux 側のファイルを直接編集できます。

> **編集は Windows 側の VS Code、実行はコンテナの中** という分担になります。
> `ws/` の下は両方から見えているので、保存すればすぐコンテナ側に反映されます。

### 自分のパッケージを作る

コンテナの中で:

```bash
cd /ws/src
ros2 pkg create --build-type ament_python my_package
cd /ws
colcon build --symlink-install
source install/setup.bash
```

以降 `ros2 run my_package ...` で自分のノードを起動できます。

### ライブラリを追加したくなったら

その場で試すだけなら:

```bash
sudo apt update && sudo apt install -y <パッケージ名>
```

（コンテナ内はパスワードなしで `sudo` できます）

ただし **コンテナを作り直すと消えます**。
今後も必要なものは `Dockerfile` の `apt-get install` の行に書き足して、
`docker compose build` でイメージを作り直してください。

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `wsl` コマンドが見つからない | Windows が古い | Windows Update を全部当てる |
| `wsl -l -v` の VERSION が 1 | WSL1 で動いている | `wsl --set-version Ubuntu-24.04 2` |
| `docker: permission denied` | docker グループの反映前 | `wsl --shutdown` して開き直す |
| `Cannot connect to the Docker daemon` | Docker が起動していない | `sudo systemctl start docker` / `sudo systemctl enable docker` |
| `bad interpreter: ...^M` | 改行コードが Windows 形式 | `dos2unix run.sh demo.sh` |
| `./run.sh: Permission denied` | 実行権限がない | `chmod +x run.sh demo.sh` |
| ビルドが途中で止まる | ネットワークかディスク不足 | `df -h /` を確認し、`./run.sh` を再実行 |
| GUI が出ない（`xeyes` も出ない） | WSL が古い | `wsl --update` → `wsl --shutdown` |
| RViz2 だけ出ない | 起動が遅いだけのことが多い | 20 秒待つ。それでも駄目ならコンテナを作り直す |
| `ros2: command not found`（スクリプトから） | 非対話シェルで設定が読まれていない | `bash -c` ではなく **`bash -lc`** を使う（[PRACTICES 2.1](PRACTICES.md#21-環境設定は-bashrc-ではなく-etcprofiled-に置き-bashrc-から読む)） |
| ノードは動くのにトピックが見えない | 通信設定（DDS）の相性 | `export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` を試す |
| 他人のロボットが勝手に見える／混線する | 同一ネットワークで ID が同じ | `ROS_DOMAIN_ID=42 ./run.sh` のように分ける |
| Gazebo が落ちる | 共有メモリ不足 | `compose.yaml` の `shm_size` を増やす（既定 2gb） |
| 全体的に重い | WSL のメモリ割り当て不足 | `.wslconfig` の `memory` を増やす（ステップ 1.5） |
| `ws/` のファイルが編集できない | UID がずれている | `id` が `uid=1000` か確認（[PRACTICES 1.3](PRACTICES.md#13-ホストとコンテナで-uid-を揃える)） |
| `claude: command not found` | PATH が通っていない | ターミナルを開き直す。それでも駄目なら `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc` |
| Claude Code のログイン用ブラウザが開かない | WSL から Windows のブラウザを起動できない | 表示された URL を手で Windows のブラウザに貼る |
| Claude Code の調子がおかしい | インストールの問題 | `claude doctor` で状態を確認、`claude install stable` で入れ直す |

### 最後の手段: 全部やり直す

**コンテナだけ作り直す**（`ws/` の中身は残る）:

```bash
cd ~/workspace/ros
docker compose down -v
docker image rm ros2-jazzy-dev
./run.sh
```

**Ubuntu ごと作り直す**（PowerShell、**中のファイルは全部消えます**）:

```powershell
wsl --unregister Ubuntu-24.04
wsl --install -d Ubuntu-24.04
```

> やり直しが怖くないことがコンテナを使う一番の理由です。
> 詰まったら早めに作り直したほうが、原因調査より速いことがよくあります。

---

## 付録 A. 用語集

**WSL2** — Windows の中で本物の Linux カーネルを動かす仕組み。
Windows と Linux が同じ PC で同時に動きます。

**WSLg** — WSL2 に含まれる、Linux のウィンドウを Windows のデスクトップに
表示する仕組み。これのおかげで RViz2 や Gazebo の画面が出ます。

**Docker** — アプリと、それが必要とする OS 環境をまとめて「箱」に詰め、
他と隔離して動かす仕組み。

**イメージ (image)** — 箱の設計図兼ひな型。`Dockerfile` から作られます。

**コンテナ (container)** — イメージから起動した、実際に動いている箱。
壊れても捨てて作り直せます。

**docker compose** — 複数の設定（共有フォルダ・ネットワーク・画面）を
`compose.yaml` に書いておいて、まとめて起動するための道具。

**バインドマウント** — ホスト側のフォルダをコンテナの中に見せること。
この環境では `ws/` を `/ws` として共有しています。

**ROS 2** — ロボット用のソフトウェア基盤。小さなプログラムを
通信で繋いでロボットを作るための仕組みと道具一式。

**ノード (node)** — ROS の中で動く 1 つのプログラム。

**トピック (topic)** — ノード同士がメッセージを流す名前付きの通信路。
`/cmd_vel`（速度指令）、`/odom`（自己位置）、`/scan`（レーザー距離計）など。

**DDS** — ROS 2 が内部で使っている通信の仕組み。
同じネットワークにいるノードを自動で見つけてくれます。

**colcon** — ROS 2 のビルドツール。`colcon build` でワークスペースを構築します。

**underlay / overlay** — ROS 本体（`/opt/ros/jazzy`）が underlay、
自分のワークスペース（`/ws/install`）が overlay。
両方を `source` することで自作パッケージが使えるようになります。

**Gazebo** — 物理シミュレータ。重力や衝突を計算して、ロボットを仮想空間で動かします。

**RViz2** — ROS の可視化ツール。ロボットの位置やセンサーの値を 3D で表示します。

**RTF (real-time factor)** — シミュレータの速度。1.0 が実時間と同じ、
0.5 なら実時間の半分の速さでしか進んでいません。

**Claude Code** — ターミナルの中で動く AI コーディング支援ツール。
ファイルの読み書き、コマンドの実行、エラーの原因調査を任せられます。
この環境自体、これを使って組み立てられました。

**TurtleBot3** — 教材としてよく使われる小型の移動ロボット。
実機とシミュレータで同じトピック構成なので、書いたコードをそのまま実機に載せられます。

---

## 付録 B. ゼロから自分で組み立てる場合の順番

ファイルをコピーするのではなく、自分で一から書いて理解したい人向けに、
この環境が積み上がっていった順番を示します。
**一度に全部書こうとせず、各段階で必ず動作確認してください。**

1. **ROS だけ動くコンテナ**
   `FROM osrf/ros:jazzy-desktop-full` と `CMD ["bash"]` だけの `Dockerfile`。
   `docker build` → `docker run -it` で入って `ros2 --version` が通ることを確認。

2. **一般ユーザーで動かす**
   ホストと同じ UID のユーザーを作る（[PRACTICES 1.3](PRACTICES.md#13-ホストとコンテナで-uid-を揃える)）。
   root のまま進めると、あとでファイルの権限で必ず詰まります。

3. **ワークスペースを共有する**
   `compose.yaml` を書き、`./ws:/ws` をマウント。
   コンテナ内で作ったファイルがホスト側で自分の所有になっているか確認。

4. **シェルの初期設定を通す**
   `source /opt/ros/jazzy/setup.bash` を `/etc/profile.d` に置く。
   対話シェルとスクリプト実行（`bash -lc`）の**両方**で `ros2` が使えるか確認
   （[PRACTICES 2.1](PRACTICES.md#21-環境設定は-bashrc-ではなく-etcprofiled-に置き-bashrc-から読む)）。

5. **GUI を通す**
   WSLg 関連のマウントと環境変数を追加し、まず `xeyes`、次に `rviz2`。
   ここが一番環境差が出る部分です（[PRACTICES 3 章](PRACTICES.md#3-wsl2--wslg-固有の壁)）。

6. **通信の設定を明示する**
   `network_mode: host`、`ROS_DOMAIN_ID`、`ROS_AUTOMATIC_DISCOVERY_RANGE`。
   talker / listener が通ることを確認。

7. **シミュレータを載せる**
   TurtleBot3 + Gazebo をインストール。`shm_size` を増やさないと落ちます。
   `/cmd_vel`・`/odom`・`/scan` がトピック一覧に出れば成功。

8. **制御コードを書く**
   まず `/odom` を購読して現在位置を表示するだけのノードから。
   次に閉ループで前進、最後にレーザーでの安全停止
   （[PRACTICES 6 章](PRACTICES.md#6-ロボット制御コードの書き方)）。

> 各段階で詰まったら、エラー出力をそのまま Claude Code に貼るのが一番速い解決法です
> （[ステップ 4.7](#47-この環境を作るときに実際に効いた使い方)）。

9. **自動化する**
   ここまでの手順を `run.sh` / `demo.sh` にまとめる。
   手順書は腐りますが、スクリプトは実行すれば腐ったことが分かります
   （[PRACTICES 7 章](PRACTICES.md#7-自動化スクリプトdemosh--runsh)）。

---

## 次に読むもの

- [README.md](README.md) — 日々の使い方、コマンドの一覧
- [PRACTICES.md](PRACTICES.md) — なぜこの作りなのか、回避策の理由
- [ROS 2 Jazzy 公式チュートリアル](https://docs.ros.org/en/jazzy/Tutorials.html) — ROS そのものの学習
- [Claude Code のドキュメント](https://docs.claude.com/en/docs/claude-code) — 設定・スラッシュコマンド・MCP など
