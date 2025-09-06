# Chatroll メッセージ削除 GitHub Actions

Chatrollメッセージを自動削除するGitHub Actionsワークフローの設定です。

## セットアップ手順

### 1. GitHub Secretsの設定

GitHubリポジトリの Settings → Secrets and variables → Actions で以下のsecretsを設定：

- `CHATROLL_USERNAME`: Chatrollのユーザー名（例: `DSI`）
- `CHATROLL_PASSWORD`: Chatrollのパスワード（例: `Stat3908@`）
- `CHATROLL_ROOM1_URL`: 1つ目のチャットルームURL（例: `https://chatroll.com/7mll`）
- `CHATROLL_ROOM2_URL`: 2つ目のチャットルームURL（例: `https://chatroll.com/3bt8`）

### 2. ワークフローの実行スケジュール

- **自動実行**: 毎日午前2時（JST）
- **手動実行**: GitHub Actions画面から「Run workflow」ボタンで実行可能

### 3. ログの確認方法

#### 成功時
1. GitHubリポジトリ → Actions タブ
2. 「Delete Chatroll Messages」ワークフロー選択
3. 実行履歴から最新の実行をクリック
4. 「delete-messages」ジョブをクリック
5. 各ステップの詳細ログを確認

#### 失敗時
- ログがArtifactsとして自動保存される（7日間保持）
- 「execution-logs」をダウンロードして詳細確認可能

### 4. 実行確認

実行が成功すると、以下のような出力が表示されます：
```
=== Processing Room 1: https://chatroll.com/7mll ===
Room loaded. Current URL: https://chatroll.com/7mll
Total messages found: 150
Deleting message 1 (remaining: 150)
...
Deleted messages in room 1: 150

=== Processing Room 2: https://chatroll.com/3bt8 ===
Room loaded. Current URL: https://chatroll.com/3bt8
Total messages found: 75
Deleting message 1 (remaining: 75)
...
Deleted messages in room 2: 75

=== Total deleted messages across all rooms: 225 ===
```

## トラブルシューティング

### よくある問題

1. **ログイン失敗**
   - Secretsの値が正しく設定されているか確認
   - Chatrollのログイン情報が変更されていないか確認

2. **メッセージが削除されない**
   - Chatrollの画面構造が変更された可能性
   - セレクタの調整が必要な場合があります

3. **タイムアウトエラー**
   - ネットワークの問題
   - 大量のメッセージがある場合の処理時間超過

### 手動実行方法

緊急時やテスト時は手動実行も可能：
1. GitHub Actions画面
2. 「Delete Chatroll Messages」選択
3. 「Run workflow」ボタンクリック
4. 「Run workflow」で実行開始

## セキュリティ注意事項

- パスワードなどの認証情報は必ずGitHub Secretsに保存
- コード内にハードコーディングしない
- ログイン情報の定期的な更新を推奨