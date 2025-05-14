import discord
from discord import app_commands
import re
from datetime import datetime
import os
import logging
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('discord_bot')

# シンプルなHTTPハンドラー
class SimpleHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        logger.info(format%args)

class ArchiveBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.guild_settings = {}
        self.load_settings()

    def load_settings(self):
        """設定をJSONファイルから読み込む"""
        try:
            if os.path.exists('guild_settings.json'):
                with open('guild_settings.json', 'r') as f:
                    self.guild_settings = json.load(f)
                    # 文字列のキーを整数に変換
                    self.guild_settings = {int(k): v for k, v in self.guild_settings.items()}
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def save_settings(self):
        """設定をJSONファイルに保存"""
        try:
            with open('guild_settings.json', 'w') as f:
                json.dump(self.guild_settings, f)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    async def setup_hook(self):
        try:
            logger.info("Setting up commands...")
            await self.tree.sync()
            logger.info("Commands setup complete!")
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}", exc_info=True)

client = ArchiveBot()

# URLを検出する正規表現パターン
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

# Tenor GIF URLを検出するパターン
TENOR_URL_PATTERN = r'https?://tenor\.com/view[^\s]*'

# プライベートチャンネルかどうかを判断する関数
def is_private_channel(channel):
    """
    チャンネルがプライベートかどうかを判断する
    @everyone に VIEW_CHANNEL 権限がない場合、プライベートチャンネルと見なす
    """
    try:
        # @everyone のロールを取得
        everyone_role = channel.guild.default_role
        
        # チャンネルの権限を確認
        permissions = channel.permissions_for(everyone_role)
        
        # VIEW_CHANNEL 権限がなければプライベート
        return not permissions.view_channel
    except Exception as e:
        logger.error(f"Error checking channel privacy: {e}", exc_info=True)
        # エラーの場合は安全のため、プライベートと見なす
        return True

@client.event
async def on_ready():
    try:
        logger.info(f'Bot {client.user} is ready')
        logger.info('Monitoring messages for URLs and files...')
        await client.tree.sync()
        await client.change_presence(activity=discord.Game(name="/help でコマンド一覧"))
    except Exception as e:
        logger.error(f"Error in on_ready: {e}", exc_info=True)

@client.tree.command(name="help", description="利用可能なコマンドの一覧を表示します")
async def help_command(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="Bot コマンド一覧",
            description="使用可能なコマンドの説明です",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="/help",
            value="このヘルプメッセージを表示します",
            inline=False
        )
        embed.add_field(
            name="/status",
            value="このサーバーでのBotの状態を表示します",
            inline=False
        )
        embed.add_field(
            name="/set_archive_channel",
            value="このサーバーのアーカイブチャンネルを設定します",
            inline=False
        )
        embed.add_field(
            name="/show_archive_channel",
            value="このサーバーの現在のアーカイブチャンネルを表示します",
            inline=False
        )
        embed.add_field(
            name="/set_privacy",
            value="プライベートチャンネルの処理方法を設定します",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Error in help command: {e}", exc_info=True)
        await interaction.response.send_message("コマンドの実行中にエラーが発生しました。", ephemeral=True)

@client.tree.command(name="status", description="このサーバーでのBotの状態を表示します")
async def status_command(interaction: discord.Interaction):
    try:
        guild_id = interaction.guild_id
        guild_settings = client.guild_settings.get(guild_id, {})
        channel_id = guild_settings.get('archive_channel_id')
        archive_private = guild_settings.get('archive_private', False)
        archive_channel = client.get_channel(channel_id) if channel_id else None
        
        embed = discord.Embed(
            title=f"Bot Status - {interaction.guild.name}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Bot名",
            value=client.user.name,
            inline=True
        )
        embed.add_field(
            name="アーカイブチャンネル",
            value=f"#{archive_channel.name if archive_channel else '未設定'}" ,
            inline=True
        )
        embed.add_field(
            name="監視状態",
            value="アクティブ" if channel_id else "アーカイブ先未設定",
            inline=True
        )
        embed.add_field(
            name="プライベートチャンネル",
            value="アーカイブする" if archive_private else "アーカイブしない",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Error in status command: {e}", exc_info=True)
        await interaction.response.send_message("ステータスの取得中にエラーが発生しました。", ephemeral=True)

@client.tree.command(name="set_archive_channel", description="このサーバーのアーカイブチャンネルを設定します")
async def set_archive_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        # サーバーIDとチャンネルIDを保存
        guild_id = interaction.guild_id
        if guild_id not in client.guild_settings:
            client.guild_settings[guild_id] = {}
        
        client.guild_settings[guild_id]['archive_channel_id'] = channel.id
        client.save_settings()
        
        embed = discord.Embed(
            title="アーカイブチャンネルを設定しました",
            description=f"このサーバーのアーカイブチャンネルを #{channel.name} に設定しました",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="チャンネルID",
            value=str(channel.id),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"Error in set_archive_channel command: {e}", exc_info=True)
        await interaction.response.send_message("チャンネルの設定中にエラーが発生しました。", ephemeral=True)

@client.tree.command(name="show_archive_channel", description="このサーバーの現在のアーカイブチャンネルを表示します")
async def show_archive_channel(interaction: discord.Interaction):
    try:
        guild_id = interaction.guild_id
        channel_id = client.guild_settings.get(guild_id, {}).get('archive_channel_id')
        
        if channel_id:
            archive_channel = client.get_channel(channel_id)
            if archive_channel:
                await interaction.response.send_message(
                    f"このサーバーのアーカイブチャンネル: #{archive_channel.name} (ID: {channel_id})"
                )
            else:
                await interaction.response.send_message("設定されているチャンネルが見つかりません。")
        else:
            await interaction.response.send_message("アーカイブチャンネルが設定されていません。/set_archive_channel で設定してください。")
    except Exception as e:
        logger.error(f"Error in show_archive_channel command: {e}", exc_info=True)
        await interaction.response.send_message("チャンネル情報の取得中にエラーが発生しました。", ephemeral=True)

# コマンド名を変更: privacy_settings -> set_privacy
@client.tree.command(name="set_privacy", description="プライベートチャンネルの処理方法を設定します")
@app_commands.describe(
    archive_private="True: プライベートチャンネルもアーカイブする, False: プライベートチャンネルをアーカイブしない（デフォルト）"
)
async def set_privacy(interaction: discord.Interaction, archive_private: bool = False):
    try:
        guild_id = interaction.guild_id
        if guild_id not in client.guild_settings:
            client.guild_settings[guild_id] = {}
        
        client.guild_settings[guild_id]['archive_private'] = archive_private
        client.save_settings()
        
        logger.info(f"Privacy settings updated for guild {guild_id}: archive_private = {archive_private}")
        
        if archive_private:
            message = "プライベートチャンネルのコンテンツもアーカイブするように設定しました。"
        else:
            message = "プライベートチャンネルのコンテンツはアーカイブしないように設定しました。"
            
        await interaction.response.send_message(message)
    except Exception as e:
        logger.error(f"Error in set_privacy command: {e}", exc_info=True)
        await interaction.response.send_message("設定の更新中にエラーが発生しました。", ephemeral=True)

@client.tree.command(name="sync_commands", description="コマンドを再同期します（管理者のみ）")
async def sync_commands(interaction: discord.Interaction):
    try:
        # 管理者権限チェック
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
            return
            
        await client.tree.sync()
        await interaction.response.send_message("コマンドを再同期しました。新しいコマンドが使用可能になりました。")
    except Exception as e:
        logger.error(f"Error in sync_commands: {e}", exc_info=True)
        await interaction.response.send_message("コマンドの同期中にエラーが発生しました。", ephemeral=True)

@client.event
async def on_message(message):
    try:
        # Botのメッセージは無視
        if message.author == client.user:
            return

        # DMは無視
        if not message.guild:
            return

        # サーバーのアーカイブ設定を取得
        guild_id = message.guild.id
        guild_settings = client.guild_settings.get(guild_id, {})
        channel_id = guild_settings.get('archive_channel_id')
        
        # アーカイブ設定がなければ無視
        if not channel_id:
            return

        # アーカイブチャンネルのメッセージは無視
        if message.channel.id == channel_id:
            return
            
        # プライベートチャンネルの処理
        is_private = is_private_channel(message.channel)
        archive_private = guild_settings.get('archive_private', False)
        
        if is_private and not archive_private:
            logger.info(f"Skipped message in private channel {message.channel.name}")
            return

        archive_channel = client.get_channel(channel_id)
        if not archive_channel:
            logger.error(f'Archive channel {channel_id} not found for guild {guild_id}')
            return

        # メッセージからURLを検出
        all_urls = re.findall(URL_PATTERN, message.content)
        
        # Tenor GIF URLを検出して除外
        tenor_urls = re.findall(TENOR_URL_PATTERN, message.content)
        
        # Tenor GIF URLを除外
        urls = [url for url in all_urls if url not in tenor_urls]
        
        # 添付ファイルを処理
        files = message.attachments
        
        if urls or files:
            embed = discord.Embed(
                title="新しいコンテンツが共有されました",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="送信者",
                value=message.author.display_name,
                inline=True
            )
            embed.add_field(
                name="元のチャンネル",
                value=message.channel.name,
                inline=True
            )
            
            if urls:
                url_list = "\n".join(urls)
                embed.add_field(
                    name="共有されたURL",
                    value=url_list,
                    inline=False
                )
            
            if files:
                file_list = "\n".join([f.filename for f in files])
                embed.add_field(
                    name="共有されたファイル",
                    value=file_list,
                    inline=False
                )
            
            embed.add_field(
                name="元のメッセージへのリンク",
                value=message.jump_url,
                inline=False
            )
            
            await archive_channel.send(embed=embed)
            
            if files:
                for file in files:
                    try:
                        await archive_channel.send(file=await file.to_file())
                    except Exception as e:
                        logger.error(f"Error sending file {file.filename}: {e}")
    except Exception as e:
        logger.error(f"Error in message handling: {e}", exc_info=True)

@client.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in {event}", exc_info=True)

if __name__ == "__main__":
    try:
        # HTTPサーバーの設定
        port = int(os.getenv('PORT', 10000))
        http_server = HTTPServer(('0.0.0.0', port), SimpleHTTPHandler)
        server_thread = threading.Thread(target=http_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        logger.info(f"Started HTTP server on port {port}")

        # Botの起動
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is not set")
        
        logger.info("Starting bot...")
        client.run(token)
    except Exception as e:
        logger.critical(f"Failed to start: {e}", exc_info=True)
        sys.exit(1)