# crane_plus_master_slave_sim

CRANE+ V2 を2台、RViz の中に並べて、**マスタースレーブ(リーダー・フォロワー)操縦を再現**するROS 2パッケージです。

* **左のアーム(リーダー)**: スライダーで動かします。人が手で動かすミニアームの代わりです。
* **右のアーム(フォロワー)**: リーダーの関節角度をコピーして、同じ姿勢になります。本物のアームの代わりです。

実機は要りません。考え方は [ShotaAk/crane_plus の PR #2](https://github.com/ShotaAk/crane_plus/pull/2) の `master_slave_controller` と同じです。そこに、KARURAミニアームで必要になる安全機能を足しています。

| 機能 | 内容 | 設定 |
|---|---|---|
| 関節の対応付け | リーダーの何番をフォロワーの何番に送るか | `leader_joints` / `follower_joints` |
| 符号の反転 | 回る向きが逆の関節を反転 | `invert` |
| ゼロ点の補正 | キャリブレーションのずれを足す | `offset` |
| 可動範囲の制限 | フォロワーの範囲外の角度は送らない | `lower_limit` / `upper_limit` |
| 速度の制限 | 急に飛ばず、決めた速さで追いつく | `max_velocity` |
| イネーブル | 有効な間だけ追従する | `enabled`、サービス `~/enable` |
| 通信切れ停止 | リーダーの角度が途切れたら、その場で止まる | `leader_timeout` |

設定はすべて [`config/master_slave.yaml`](crane_plus_master_slave_sim/config/master_slave.yaml) にあります。

## 動作環境

* Ubuntu 22.04 + ROS 2 Humble
* 本家 [rt-net/crane_plus](https://github.com/rt-net/crane_plus) の `humble` ブランチ(アームの形のデータを使います)

## インストール

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/ippo100-bit/crane_plus_master_slave_sim.git
git clone -b humble https://github.com/rt-net/crane_plus.git
cd ~/ros2_ws
rosdep install -r -y -i --from-paths src
colcon build --symlink-install
source install/setup.bash
```

`vcstool` を使う場合は、`git clone -b humble ...` の代わりに `vcs import src < src/crane_plus_master_slave_sim/crane_plus.repos` でも取得できます。

## 動かし方

```bash
ros2 launch crane_plus_master_slave_sim master_slave_rviz.launch.py
```

RViz と、スライダーのウィンドウが開きます。スライダーを動かすと、左のアームが動き、右のアームが少し遅れて同じ姿勢になります。

### 試してみること

**追従を止める・再開する(イネーブルスイッチ)**

```bash
ros2 service call /master_slave_bridge/enable std_srvs/srv/SetBool "{data: false}"   # 止める
ros2 service call /master_slave_bridge/enable std_srvs/srv/SetBool "{data: true}"    # 再開
```

止めている間にスライダーを大きく動かしてから再開すると、フォロワーは一気に飛ばず、`max_velocity` の速さで追いつきます。

**向きを反転する**

`config/master_slave.yaml` の `invert` を `[false, true, false, false, false]` にして起動し直すと、肩の関節だけ逆向きに動きます。

**ゆっくり追従させる**

`max_velocity` を `0.3` などに下げると、フォロワーの遅れがよくわかります。

## 構成

```
crane_plus_master_slave_sim/
├── crane_plus.repos                 本家crane_plus(humble)の取得用
└── crane_plus_master_slave_sim/     ROS 2パッケージ
    ├── crane_plus_master_slave_sim/
    │   ├── master_slave_bridge.py   リーダー → フォロワーの橋渡しノード
    │   └── mapping.py               角度の変換(対応付け・反転・制限)
    ├── config/master_slave.yaml     設定
    ├── launch/master_slave_rviz.launch.py
    ├── rviz/master_slave.rviz
    └── test/test_mapping.py
```

ノードとトピックのつながり:

```
joint_state_publisher_gui ──/leader/joint_states──▶ master_slave_bridge ──/follower/joint_states──▶ robot_state_publisher(follower)
          │                                                                                                   │
          └────────────────────────▶ robot_state_publisher(leader) ──TF──▶ RViz ◀──TF───────────────────────────┘
```

## KARURAミニアームへの応用

* `/leader/joint_states` を、スライダーではなく **Picoから角度を受け取るノード** に置き換えれば、ミニアームがそのままリーダーになります。その場合は `leader_gui:=false` で起動すると、スライダーが立ち上がりません。

  ```bash
  ros2 launch crane_plus_master_slave_sim master_slave_rviz.launch.py leader_gui:=false
  ```
* `follower_joints` と可動範囲を本物のアームに合わせて、`/follower/joint_states` の代わりに本物のアームの位置指令に送れば、実機の追従になります。
