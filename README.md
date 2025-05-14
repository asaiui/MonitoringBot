# MonitoringBot

MonitoringBot は Discord サーバー内で共有されたリンクやファイルを自動的に収集し、指定されたアーカイブチャンネルに保存する Discord Bot です。

## 特徴

- URLとファイルの自動収集と保存
- アーカイブ先チャンネルの柔軟な設定
- Tenor GIF URLの自動除外
- プライベートチャンネルの自動検出と選択的アーカイブ
- サーバーごとの個別設定

## 招待リンク

以下のリンクを Discord に張り付けると Bot を招待することができます。

https://discord.com/oauth2/authorize?client_id=1338357316713582634

## 使い方

1. `/status` コマンドで Bot が正常に動作しているか確認
2. `/set_archive_channel` コマンドでアーカイブ先チャンネルを設定
3. 必要に応じて `/privacy_settings` コマンドでプライベートチャンネルの扱いを設定

以降、サーバー内でURLやファイルが共有されると、自動的に指定したアーカイブチャンネルに保存されます。

※Bot が Discord 上でオフラインの場合はサーバーに障害が発生している可能性があります。再度 `/status` で確認してください。

## コマンド一覧

| コマンド | 説明 | 使用例 |
|--------|------|-------|
| `/help` | 利用可能なコマンドの一覧を表示 | `/help` |
| `/status` | Bot の状態と設定を表示 | `/status` |
| `/set_archive_channel` | アーカイブ先チャンネルを設定 | `/set_archive_channel #アーカイブ` |
| `/show_archive_channel` | 現在のアーカイブチャンネルを表示 | `/show_archive_channel` |
| `/privacy_settings` | プライベートチャンネルの処理方法を設定 | `/privacy_settings false` |
| `/sync_commands` | コマンドを再同期（管理者のみ） | `/sync_commands` |

## 詳細設定

### プライベートチャンネルの扱い

- デフォルトでは、@everyone ロールに閲覧権限がないチャンネル（プライベートチャンネル）のコンテンツはアーカイブされません
- `/privacy_settings true` を実行すると、プライベートチャンネルのコンテンツもアーカイブされるようになります
- `/privacy_settings false` を実行すると、プライベートチャンネルのコンテンツはアーカイブされなくなります

### 除外されるコンテンツ

現在、以下のコンテンツは自動的にアーカイブから除外されます：

- Tenor GIF URL（`https://tenor.com/view` から始まる URL）
- プライベートチャンネルのコンテンツ（設定による）
