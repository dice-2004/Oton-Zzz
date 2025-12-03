#!/usr/bin/env python3
"""
設定ファイル管理モジュール
config.jsonから睡眠検出パラメータを読み込み
"""

import json
import os
import shutil


class ConfigManager:
    """設定ファイルの読み込み・保存を管理"""

    def __init__(self, config_file='config/config.json', template_file='config/config_template.json'):
        """
        初期化

        Args:
            config_file: 実際の設定ファイル
            template_file: テンプレートファイル
        """
        self.config_file = config_file
        self.template_file = template_file
        self.config = None

        # 設定ファイルがなければテンプレートからコピー
        if not os.path.exists(self.config_file):
            if os.path.exists(self.template_file):
                print(f"⚙️  設定ファイルが見つかりません。{self.template_file} からコピーします...")
                shutil.copy(self.template_file, self.config_file)
                print(f"✓ {self.config_file} を作成しました")
            else:
                raise FileNotFoundError(f"テンプレートファイル {self.template_file} が見つかりません")

        # 設定を読み込み
        self.load()

    def load(self):
        """設定ファイルを読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✓ 設定ファイル {self.config_file} を読み込みました")
            return self.config
        except Exception as e:
            raise Exception(f"設定ファイルの読み込みに失敗しました: {e}")

    def save(self):
        """現在の設定をファイルに保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✓ 設定を {self.config_file} に保存しました")
            return True
        except Exception as e:
            print(f"✗ 設定の保存に失敗しました: {e}")
            return False

    def get_sleep_detection_params(self):
        """睡眠検出パラメータを取得"""
        return self.config.get('sleep_detection', {})

    def update_sleep_detection_params(self, **kwargs):
        """
        睡眠検出パラメータを更新

        Args:
            **kwargs: 更新するパラメータ（blink_threshold, gauge_max など）
        """
        if 'sleep_detection' not in self.config:
            self.config['sleep_detection'] = {}

        for key, value in kwargs.items():
            self.config['sleep_detection'][key] = value
            print(f"  {key}: {value}")

        return self.save()

    def get_system_params(self):
        """システムパラメータを取得"""
        return self.config.get('system', {})

    def get_hardware_params(self):
        """ハードウェアパラメータを取得"""
        return self.config.get('hardware', {})

    def print_params(self):
        """現在のパラメータを表示"""
        print("\n" + "="*60)
        print("現在の設定:")
        print("="*60)

        print("\n【睡眠検出パラメータ】")
        for key, value in self.get_sleep_detection_params().items():
            print(f"  {key}: {value}")

        print("\n【システムパラメータ】")
        for key, value in self.get_system_params().items():
            print(f"  {key}: {value}")

        print("\n【ハードウェアパラメータ】")
        hw_params = self.get_hardware_params()
        for key, value in hw_params.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        print("="*60 + "\n")


if __name__ == '__main__':
    """テスト用"""
    print("ConfigManager テスト\n")

    config_mgr = ConfigManager()
    config_mgr.print_params()

    # パラメータ更新テスト
    print("パラメータを更新します...")
    config_mgr.update_sleep_detection_params(
        blink_threshold=0.6,
        gauge_max=6.0
    )

    print("\n更新後:")
    config_mgr.print_params()
