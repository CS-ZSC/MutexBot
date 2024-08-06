import asyncio
import os
import socketserver
import threading
from http.server import SimpleHTTPRequestHandler
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from utils import gdrive

load_dotenv('.env')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("TOKEN not found in environment variables")

try:
    drive, gspread_client = gdrive()
except Exception as e:
    print(f"Failed to initialize Google Drive and Sheets: {e}")
    exit(1)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.event
async def on_member_join(member):
    _id = member.id
    _username = member.name
    print(f"Member joined: ID={_id}, Username={_username}")
    try:
        sheet = gspread_client.open("Mutex").worksheet("default")
        print("Worksheet 'default' opened successfully.")
        records = sheet.get_all_records()

        for row in records:
            if str(row['UserID']) == str(_username) or str(row['UserID']) == str(_id):
                role_name = row['RoleName']
                print(f"Match found: RoleName={role_name}")
                guild = member.guild
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    new_nickname = f"{row['UserName']}-{row['TeamName']}"
                    print(f"New nickname: {new_nickname}")
                    await asyncio.gather(
                        member.add_roles(role),
                        member.edit(nick=new_nickname),
                        member.send(f'Welcome to Mutex server. Wishing you all the best 😀. '
                                    f'You have gained a role to be a {role_name}.')
                    )
                    print(f"Role '{role_name}' added and nickname set for member '{_username}'.")
                else:
                    print(f'Role "{role_name}" not found in guild "{guild.name}"')
                break
        else:
            print(f"No match found for member ID={_id} or Username={_username}.")
            await member.send(
                'You are not registered. Please register at (form link)['
                'https://docs.google.com/forms/d/e/1FAIpQLSdiRkiyYPBGjRiTwJDOuY-K8cFPCqvugurz0yNcRcJjZ5DUkg/viewform] '
                'or contact us.')
            await member.kick(reason='You are not registered. Please register at (form link)['
                                     'https://docs.google.com/forms/d/e/1FAIpQLSdiRkiyYPBGjRiTwJDOuY'
                                     '-K8cFPCqvugurz0yNcRcJjZ5DUkg/viewform]'
                                     'or contact us.')
    except Exception as e:
        print(f'An error occurred: {e}')


@bot.tree.command(name="submit-report", description="Submit a report with a file and team name")
@app_commands.describe(team_name="Name of the team", report_file="File containing the report")
async def submit_report(interaction: discord.Interaction, team_name: str, report_file: discord.Attachment):
    await interaction.response.defer(ephemeral=True)

    print(f"Submit report command invoked: team_name={team_name}, report_file={report_file.filename}")

    try:
        if report_file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument"
                                                               ".wordprocessingml.document", "application/msword",
                                            "application/vnd.google-apps.document"]:
            print(f"Invalid file type: {report_file.content_type}")
            await interaction.followup.send("Invalid file type. Please upload a PDF file.")
            return

        file_content = await report_file.read()
        print(f"File content read successfully. File size: {len(file_content)} bytes")

        file_drive = drive.CreateFile({
            'title': f'{team_name}_{report_file.filename}',
            "parents": [{"id": os.getenv('FOLDER_ID')}]
        })
        print(f"Drive file created with title: {team_name}_{report_file.filename}")

        if report_file.content_type == "text/plain":
            file_drive.SetContentString(file_content.decode('utf-8'))
        else:
            file_path = f"./{team_name}_{report_file.filename}"
            with open(file_path, 'wb') as f:
                f.write(file_content)
            print(f"File written to temporary path: {file_path}")
            file_drive.SetContentFile(file_path)
            os.remove(file_path)
            print(f"File uploaded and temporary file removed: {file_path}")

        file_drive.Upload()

        file_id = file_drive['id']
        print(f"Uploaded file ID: {file_id}")

        file_drive.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'
        })

        shareable_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        print(f"Shareable link generated: {shareable_link}")

        # Acknowledge the submission
        await interaction.followup.send(
            f"Report for team {team_name} has been submitted successfully.\n"
            f"Google Drive link: {shareable_link}"
        )
        print("Acknowledgement sent to user.")
    except Exception as error:
        print(f"Failed to upload report: {error}")
        await interaction.followup.send(f"Failed to upload report: {error}")


class MyHttpRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = "I am running good (Mutex Bot)"
        self.wfile.write(bytes(html, "utf8"))


def create_server():
    port = 8000
    handler_object = MyHttpRequestHandler
    my_server = socketserver.TCPServer(("", port), handler_object)

    print("serving at port:" + str(port))
    my_server.serve_forever()


threading.Thread(target=create_server).start()
bot.run(TOKEN)
