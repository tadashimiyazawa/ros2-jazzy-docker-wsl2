# ROS 2 Jazzy 開発環境 (Docker / WSL2)

Ubuntu 24.04 (WSL2) 上の Docker で動く ROS 2 **Jazzy Jalisco** 環境です。
ホスト側には何もインストールされないため、環境を汚さず、削除も `docker compose down` だけで済みます。

**初めてこの環境を作る場合**は [SETUP.md](SETUP.md) を見てください。
WSL2 の導入から Docker・Claude Code のインストール、動作確認までを順に追える手順書です。

設計の意図・回避策の理由・再利用できる方針は [PRACTICES.md](PRACTICES.md) にまとめてあります。

## 構成

```
~/workspace/ros/
├── Dockerfile      osrf/ros:jazzy-desktop-full + 開発ツール一式
├── compose.yaml    GUI(WSLg) / ネットワーク / ボリューム設定
├── run.sh          コンテナに入るヘルパ
└── ws/             ROS 2 ワークスペース（コンテナ内の /ws にマウント）
    └── src/        ここにパッケージを置く
```

`ws/` はホストとコンテナで共有されます。**エディタはホスト側で使い、ビルドと実行はコンテナ内**という使い方を想定しています。

## 使い方

```bash
cd ~/workspace/ros
./run.sh
```

初回のみイメージをビルドします（数分）。2回目以降は即座にシェルが開きます。
別ターミナルでもう一度 `./run.sh` を実行すると、同じコンテナに追加のシェルが繋がります。

コンテナ内では `/opt/ros/jazzy/setup.bash` が自動で source 済みです。

```bash
ros2 run demo_nodes_cpp talker      # 別シェルで listener
rviz2                                # WSLg でウィンドウが開く
```

停止・削除:

```bash
docker compose down          # 停止（ws/ の中身は残る）
docker compose down -v       # ビルドキャッシュも削除
```

## パッケージの作り方

```bash
cd /ws/src
ros2 pkg create --build-type ament_python my_package
cd /ws
colcon build --symlink-install
source install/setup.bash
```

`--symlink-install` を付けると Python ファイルの変更が再ビルドなしで反映されます。
`install/`・`build/`・`log/` はコンテナ内で生成されますが、ホスト側の `ws/` にも現れます（`.gitignore` 済み）。

## 覚えておくと便利な点

**GUI** — WSLg 経由で RViz2 / Gazebo / rqt がそのまま開きます。追加の X サーバは不要です。

ただしこのマシンの WSLg の Xwayland は DRI3 に対応しておらず (`screen 0 does not appear
to be DRI3 capable`)、OpenGL は GPU ではなくソフトウェア実装 (llvmpipe) で動きます。
コンテナはホストと同じ X server を使うため、これは WSL 上で直接 ROS を動かした場合も同じです。
RViz2 は 22 コアで問題なく動きますが、Gazebo の重いシーンは遅くなります。
GPU パススルー (`/dev/dxg` とドライバの受け渡し) の設定自体は済ませてあるので、
WSL / GPU ドライバ側が対応すれば自動的に効きます。

**ネットワーク** — `network_mode: host` なので、同じ LAN 上の別マシンや実機ロボットの ROS 2 ノードと自動で相互検出します。検出範囲は `ROS_AUTOMATIC_DISCOVERY_RANGE: SUBNET` で指定しています
（`LOCALHOST` でコンテナ内に閉じる、`OFF` で完全に隔離）。
他の人と ROS を使う環境を共有している場合は、混線を避けるため `ROS_DOMAIN_ID` を設定してください:

```bash
ROS_DOMAIN_ID=42 ./run.sh
```

**DDS の切り替え** — 既定は Fast DDS です。CycloneDDS も入れてあるので切り替えられます:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

**実機接続 (USB/シリアル)** — WSL2 では Windows 側で USB デバイスを WSL に接続する必要があります。PowerShell (管理者) で:

```powershell
usbipd list
usbipd attach --wsl --busid <BUSID>
```

そのうえで `compose.yaml` の `devices:` に `- /dev/ttyUSB0:/dev/ttyUSB0` のように追記し、
`docker compose up -d --force-recreate` で反映します。

**依存関係の解決** — `src/` に持ってきたパッケージの依存を入れる場合:

```bash
sudo apt update && rosdep install --from-paths /ws/src --ignore-src -r -y
```

コンテナ内の `rosdev` ユーザはパスワードなしで `sudo` できます。ただし `apt` で入れたものはコンテナを作り直すと消えるため、恒久的に必要なものは `Dockerfile` に追記してください。

## デモを再現する

### 一発で動かす

```bash
cd ~/workspace/ros
./demo.sh
```

Gazebo の起動 → RViz2 の起動 → ロボットの自律走行（120秒）まで自動で走ります。
Gazebo の画面も見たい場合は `./demo.sh --gui`。終了は `./demo.sh --stop`。

初回だけイメージのビルドが走ります（ベースイメージ 6.35GB のダウンロードを含めて 15 分ほど）。

### 手で順番に動かす

中で何が起きているか追いたい場合は、ターミナルを3つ開いてそれぞれで `./run.sh` を実行し、

```bash
# ターミナル1 — シミュレータ
ros2 launch /ws/launch/tb3_headless.launch.py

# ターミナル2 — 可視化
rviz2 -d /opt/ros/jazzy/share/turtlebot3_gazebo/rviz/tb3_gazebo.rviz

# ターミナル3 — 操作
python3 /ws/scripts/robot.py status
python3 /ws/scripts/robot.py forward 1.0
python3 /ws/scripts/robot.py wander 120
```

### 別のマシンで再現する

必要なのはこのディレクトリ一式（`Dockerfile` / `compose.yaml` / `run.sh` / `demo.sh` / `ws/`）だけです。
`ws/build`・`ws/install`・`ws/log`・`.wslgpu/` は生成物なのでコピー不要です。

前提は WSL2 + Ubuntu 24.04 + Docker、そしてホスト側 UID が 1000 であること
（違う場合は `compose.yaml` の `UID` / `GID` と、`.cache` 系のパスを合わせてください）。
WSL2 以外の Linux で動かす場合は、`compose.yaml` の WSLg 関連のマウントと `/dev/dxg` を
通常の X11 の設定（`/tmp/.X11-unix` のマウントと `xhost +local:`）に置き換えます。

## シミュレータ上のロボット（TurtleBot3 / Gazebo）

turtlesim より実機に近い題材として、TurtleBot3 を Gazebo Harmonic 上で動かせます。
`/cmd_vel`（速度指令）・`/odom`（オドメトリ）・`/scan`（LiDAR）・`/tf` という、
実機の移動ロボットとまったく同じインターフェースが出てくるので、
ここで書いた制御コードはそのまま実機に載せられます。

### 起動

**ターミナル1 — シミュレータ:**

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Gazebo のウィンドウが開き、障害物が置かれた世界に TurtleBot3 が出ます。

GPU 描画が効かない環境ですが、実測でシミュレーション速度 (real-time factor) は **約 0.69**、
つまり実時間の 7 割程度で動きます。学習用途では十分です。
Gazebo の画面を出さない場合は **約 0.81** で、GUI のコストは 15% 程度でした。

速度を優先する場合は、GUI なしで起動する launch ファイルを用意してあります:

```bash
ros2 launch /ws/launch/tb3_headless.launch.py
ros2 launch /ws/launch/tb3_headless.launch.py world:=empty_world.world model:=waffle
```

`turtlebot3_gazebo` の launch ファイルは Gazebo GUI を必ず起動する作りで、
引数では止められず、GUI を kill すると launch 全体が落ちます（`on_exit_shutdown`）。
そのため GUI を含まない構成を別ファイルにしています。

速度は自分で測れます:

```bash
python3 /ws/scripts/sim_speed.py
```

**ターミナル2 — RViz2 で可視化:**

```bash
rviz2 -d /opt/ros/jazzy/share/turtlebot3_gazebo/rviz/tb3_gazebo.rviz
```

ロボットのモデルと LiDAR の点群が表示されます。Gazebo の画面より軽いので、
ヘッドレス起動と組み合わせるのがおすすめです。

**ターミナル3 — 手動操作:**

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

### スクリプトから動かす

`ws/scripts/robot.py` は `/odom` で閉ループ制御する操作ツールです。
`/scan` を見て障害物の手前で必ず止まるので、指令ミスで壁に突っ込むことはありません。

```bash
python3 /ws/scripts/robot.py status        # 現在位置と前方の障害物までの距離
python3 /ws/scripts/robot.py forward 1.5   # 1.5 m 前進
python3 /ws/scripts/robot.py turn -90      # 右に 90 度旋回
python3 /ws/scripts/robot.py square 1.0    # 一辺 1 m の正方形を走る
python3 /ws/scripts/robot.py wander 120    # 120 秒間、障害物を避けて自律走行
```

トピック名が違うロボットには `--cmd-topic` / `--odom-topic` / `--scan-topic` で合わせられます。

### 別の世界・別モデル

```bash
ros2 launch turtlebot3_gazebo empty_world.launch.py              # 何もない平面
TURTLEBOT3_MODEL=waffle ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

既定は `burger`（`Dockerfile` の `TURTLEBOT3_MODEL`）です。`waffle` はカメラ付きです。

### 自律ナビゲーション（地図を作って目的地へ行く）

Nav2 と SLAM は未インストールです。試す場合は `Dockerfile` に追記してビルドしてください:

```
ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox ros-jazzy-turtlebot3-navigation2
```

## 動作確認済みの内容

- `ros2` / `colcon` / `rosdep`（340パッケージ）
- talker → listener のトピック通信
- RViz2 の GUI 起動（WSLg、OpenGL 4.5）
- `colcon build --symlink-install` と overlay の source
- `ws/` に生成されるファイルがホストユーザ (uid 1000) の所有になること
- TurtleBot3 の Gazebo シミュレーション（RTF 0.69 / ヘッドレス 0.81）と、
  `robot.py` によるオドメトリ閉ループ走行・LiDAR での障害物回避

## この環境固有の注意点

ホストの Docker は snap 版のため、`/usr` 以下をコンテナに bind mount できません。
そのため以下の回避策を入れています（`Dockerfile` / `compose.yaml` のコメント参照）:

- `/usr/lib/wsl/lib` の GPU ライブラリ3つは、`run.sh` が `.wslgpu/` に退避してイメージに焼き込む
- Windows のドライバストアは `/mnt/c/...` 経由でマウント
- `/tmp/.X11-unix` はホスト側も bind mount のため中身が見えず、`/mnt/wslg/.X11-unix` を直接マウント
