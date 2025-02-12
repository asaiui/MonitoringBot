import discord
from discord import app_commands
import re
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# ログ設定
def setup_logger():
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)
    
    # ファイルハンドラー（ログローテーション付き）
    file_handler = RotatingFileHandler(
        'discord_bot.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s: %(message)s'
    ))
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s: %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

class ArchiveBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.archive_channel_id = None  # 起動時にNullに設定
        self.logger = logger

    async def setup_hook(self):
        try:
            self.logger.info("Setting up commands...")
            await self.tree.sync()
            self.logger.info("Commands setup complete!")
        except Exception as e:
            self.logger.error(f"Error in setup_hook: {e}", exc_info=True)

client = ArchiveBot()

# URLを検出する正規表現パターン
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

# メッセージが送信されたときのイベントハンドラ
@client.event
async def on_ready():
    try:
        client.logger.info(f'Bot {client.user} is ready')
        client.logger.info('Monitoring messages for URLs and files...')
        
        # 環境変数からチャンネルIDを読み込む
        channel_id = os.getenv('ARCHIVE_CHANNEL_ID')
        if channel_id:
            client.archive_channel_id = int(channel_id)
            client.logger.info(f'Loaded archive channel ID: {channel_id}')
        
        # コマンドを同期
        await client.tree.sync()
        client.logger.info("Commands synced successfully!")
        
        # Botのステータスを設定
        await client.change_presence(activity=discord.Game(name="/help でコマンド一覧"))
    except Exception as e:
        client.logger.error(f"Error in on_ready: {e}", exc_info=True)

# クライアントのインスタンス化
client = ArchiveBot()

# URLを検出する正規表現パターン
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

# メッセージが送信されたときのイベントハンドラ
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print('Monitoring messages for URLs and files...')
    
    # コマンドを同期
    try:
        print("Syncing commands...")
        await client.tree.sync()
        print("Commands synced successfully!")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    # Botのステータスを設定
    await client.change_presence(activity=discord.Game(name="/help でコマンド一覧"))

# ヘルプコマンド
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
            value="Botの現在の状態を表示します",
            inline=False
        )
        embed.add_field(
            name="/set_archive_channel",
            value="アーカイブチャンネルを設定します",
            inline=False
        )
        embed.add_field(
            name="/show_archive_channel",
            value="現在のアーカイブチャンネルを表示します",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in help command: {e}")
        await interaction.response.send_message("コマンドの実行中にエラーが発生しました。", ephemeral=True)

# Botのステータスを表示するコマンド
@client.tree.command(name="status", description="Botの状態を表示します")
async def status_command(interaction: discord.Interaction):
    try:
        archive_channel = client.get_channel(client.archive_channel_id)
        
        embed = discord.Embed(
            title="Bot Status",
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
            value="アクティブ",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in status command: {e}")
        await interaction.response.send_message("ステータスの取得中にエラーが発生しました。", ephemeral=True)

# アーカイブチャンネルを設定するコマンド
@client.tree.command(name="set_archive_channel", description="アーカイブチャンネルを設定します")
async def set_archive_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    try:
        client.archive_channel_id = channel.id
        
        embed = discord.Embed(
            title="アーカイブチャンネルを設定しました",
            description=f"アーカイブチャンネルを #{channel.name} に設定しました",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="チャンネルID",
            value=str(channel.id),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in set_archive_channel command: {e}")
        await interaction.response.send_message("チャンネルの設定中にエラーが発生しました。", ephemeral=True)

# 現在のアーカイブチャンネルを表示するコマンド
@client.tree.command(name="show_archive_channel", description="現在のアーカイブチャンネルを表示します")
async def show_archive_channel(interaction: discord.Interaction):
    try:
        archive_channel = client.get_channel(client.archive_channel_id)
        if archive_channel:
            await interaction.response.send_message(
                f"現在のアーカイブチャンネル: #{archive_channel.name} (ID: {client.archive_channel_id})"
            )
        else:
            await interaction.response.send_message("アーカイブチャンネルが設定されていません。/set_archive_channel で設定してください。")
    except Exception as e:
        print(f"Error in show_archive_channel command: {e}")
        await interaction.response.send_message("チャンネル情報の取得中にエラーが発生しました。", ephemeral=True)

# メッセージをアーカイブするイベントハンドラ
@client.event
async def on_message(message):
    try:
        # Botのメッセージは無視
        if message.author == client.user:
            return

        # アーカイブチャンネルのメッセージは無視
        if message.channel.id == client.archive_channel_id:
            return

        archive_channel = client.get_channel(client.archive_channel_id)
        if not archive_channel:
            print(f'Error: Archive channel {client.archive_channel_id} not found')
            return

        # メッセージからURLを検出
        urls = re.findall(URL_PATTERN, message.content)
        
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
                        print(f'Error sending file {file.filename}: {e}')
    except Exception as e:
        print(f"Error in message handling: {e}")

# エラーハンドリング
@client.event
async def on_error(event, *args, **kwargs):
    client.logger.error(f"Error in {event}", exc_info=True)

if __name__ == "__main__":
    try:
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is not set")
        
        client.logger.info("Starting bot...")
        client.run(token)
    except Exception as e:
        client.logger.critical(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)