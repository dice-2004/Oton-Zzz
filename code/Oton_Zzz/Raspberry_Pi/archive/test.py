import subprocess
import time

def send_ir_continuous(scancode, interval=0.5):
    """
    LIRCサービスを使わず、カーネルドライバ経由でNECフォーマットを継続送信する
    scancode: 0x20DF10EF のような16進数文字列または数値
    interval: 送信間隔（秒）
    """
    # 数値なら文字列に変換
    if isinstance(scancode, int):
        code_str = f"{scancode:#x}"
    else:
        code_str = scancode

    print(f"コード {code_str} の継続送信を開始します。")
    print("停止するには 'Ctrl + C' を押してください。")

    try:
        while True:
            # ir-ctlコマンドを実行
            # check=Trueを入れるとエラー時にPythonが止まるため、
            # 連続送信時は通信エラーを無視して次へ進むようtry-exceptで囲むのが安全です
            try:
                subprocess.run(
                    ["ir-ctl", "-d", "/dev/lirc0", "-S", f"nec:{code_str}"],
                    check=True,
                    stdout=subprocess.DEVNULL, # 送信時のログを少し静かにする
                    stderr=subprocess.DEVNULL
                )
                print(f"送信 -> {code_str}")
            except subprocess.CalledProcessError:
                print("送信エラー (再試行します)")

            # 指定した時間待機 (秒)
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n停止しました。")

# 実行例
if __name__ == "__main__":
    # interval=0.5 で 0.5秒ごとに送信し続けます
    send_ir_continuous(0x20DF10EF, interval=0.5)
