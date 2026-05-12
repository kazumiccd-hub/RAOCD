# RAOCD

Renesas RAシリーズ向けのOpenOCD書き込みGUIアプリです。

## 機能

- OpenOCD実行ファイルのパスを選択
- 書き込み対象ファイル（HEX/BIN/ELF/SREC/MOTなど）のパスを選択
- `Write`ボタンで次のOpenOCDコマンドを実行

```bash
openocd -f interface/cmsis-dap.cfg -f target/renesas_ra.cfg -c "program filename.hex verify reset exit"
```

- 実行ログをGUI上のテキストボックスに表示

## セットアップ

Python 3を用意し、依存パッケージをインストールします。

```bash
python3 -m pip install -r requirements.txt
```

Linux環境でTkinterが入っていない場合は、OSのパッケージマネージャでTkinterもインストールしてください。

```bash
sudo apt install python3-tk
```

OpenOCDは別途インストールし、CMSIS-DAPデバッガを接続してください。

## 実行方法

```bash
python3 raocd_gui.py
```

1. `OpenOCD Path`でOpenOCD実行ファイルを選択します。PATHが通っている場合は初期値の`openocd`のまま使用できます。
2. `Binary File`で書き込み対象ファイルを選択します。
3. `Write`ボタンを押すと、`interface/cmsis-dap.cfg`と`target/renesas_ra.cfg`を使ってOpenOCDが起動し、`program <選択ファイル> verify reset exit`を実行します。
4. OpenOCDの標準出力と標準エラー出力は画面下部の`Execution Log`に表示されます。

## テスト

```bash
python3 -m unittest
```
