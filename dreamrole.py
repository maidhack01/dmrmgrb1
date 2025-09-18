import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from flask import Flask
import threading
import requests
import os
import itertools
import math

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = 5000

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Role Data ----------------
roles_data = {
    "ทั่วไป": [
        {"name": "🌌 ชาวโลกแห่งฝัน (Dreamer)", "desc": "สมาชิกทั่วไปของเซิร์ฟเวอร์ เป็นพื้นฐานสำหรับทุกคน"}
    ],
    "สายดูแล": [
        {"name": "👑 Dream Council", "desc": "ผู้ปกครองสูงสุด ตัดสินใจเรื่องสำคัญทั้งหมด"},
        {"name": "🌙 ผู้เฝ้าฝัน (Dream Watcher)", "desc": "ผู้ดูแลความสงบเรียบร้อย"},
        {"name": "☀️ ผู้เดินทางในฝัน (Dream Traveler)", "desc": "ช่วยจัดกิจกรรมและคอยช่วยเหลือสมาชิก"},
        {"name": "⭐ นักสร้างฝัน (Dream Creator)", "desc": "สร้างไอเดีย กิจกรรม และคอนเทนต์"},
        {"name": "💤 ผู้หลับลึก (Deep Sleeper)", "desc": "ผู้ช่วยเหลือเฉพาะกิจ ตรวจสอบความผิดปกติ"}
    ],
    "เกมเมอร์/นักวาด": [
        {"name": "👾 เกมเมอร์แห่งฝัน (Dream Gamer)", "desc": "สมาชิกที่เล่นเกมและกิจกรรมเกม"},
        {"name": "🎨 นักวาดแห่งฝัน (Dream Artist)", "desc": "นักวาดและสายศิลปะ แชร์งานสร้างสรรค์"},
        {"name": "🌠 นักสำรวจดาว (Star Explorer)", "desc": "นักสำรวจ ชอบลองอะไรใหม่ ๆ"},
        {"name": "☁️ นักเดินเมฆ (Cloud Walker)", "desc": "นักสร้างแรงบันดาลใจ โพสต์คอนเทนต์ฝัน ๆ"}
    ]
}

# ---------------- Rainbow Gradient ----------------
def rainbow_color(index, total, shift=0):
    """สร้างสี Rainbow ไล่เฉด"""
    if total == 0:
        total = 1
    frequency = 2 * math.pi / total
    r = int(math.sin(frequency * index + 0 + shift) * 127 + 128)
    g = int(math.sin(frequency * index + 2 + shift) * 127 + 128)
    b = int(math.sin(frequency * index + 4 + shift) * 127 + 128)
    return discord.Color.from_rgb(r, g, b)

# ---------------- Embed Function ----------------
def create_embed(category, shift=0):
    roles_list = roles_data[category]
    total_roles = len(roles_list)
    embed = discord.Embed(
        title=f"🌌 {category} ในโลกแห่งความฝัน",
        description=f"บทบาทหมวด {category}",
        color=rainbow_color(0, total_roles, shift)
    )
    for i, role in enumerate(roles_list):
        embed.add_field(
            name=role["name"],
            value=role["desc"],
            inline=False
        )
        embed.color = rainbow_color(i, max(total_roles-1,1), shift)
    embed.set_image(url="https://i.imgur.com/NZ8k2yG.jpg")
    embed.set_thumbnail(url="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif")
    embed.set_footer(text="✨ โลกแห่งความฝัน • Dream Realm")
    return embed

# ---------------- Interactive Buttons ----------------
class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        for cat in roles_data.keys():
            button = Button(label=cat, style=discord.ButtonStyle.blurple)
            button.callback = self.make_callback(cat)
            self.add_item(button)

    def make_callback(self, category):
        async def callback(interaction):
            embed = create_embed(category)
            await interaction.response.edit_message(embed=embed)
        return callback

# ---------------- On Ready ----------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    change_status.start()
    ping_flask.start()
    update_embed_colors.start()

# ---------------- Command !roles ----------------
channel_messages = {}

@bot.command()
async def roles(ctx):
    allowed_channels = ["roles"]
    if str(ctx.channel) not in allowed_channels and ctx.channel.id not in allowed_channels:
        await ctx.send("❌ คำสั่งนี้ใช้ได้เฉพาะช่อง #roles เท่านั้น", delete_after=10)
        return
    view = RoleView()
    embed = create_embed("ทั่วไป")
    msg = await ctx.send(embed=embed, view=view)
    channel_messages[ctx.channel.id] = ("ทั่วไป", msg, 0)  # เก็บ shift

# ---------------- Flask ----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running! ✅"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ---------------- Ping Monitor ----------------
@tasks.loop(minutes=4)
async def ping_flask():
    try:
        requests.get(f"http://127.0.0.1:{PORT}/")
    except:
        pass

# ---------------- Dynamic Status Loop ----------------
status_cycle = itertools.cycle([
    (discord.ActivityType.idle, "อยู่ในโลกแห่งความฝัน 🌌"),
    (discord.ActivityType.playing, "กำลังเล่นกับสมาชิก 🌠"),
    (discord.ActivityType.watching, "สมาชิกในโลกแห่งความฝัน 🌙")
])

@tasks.loop(seconds=60)
async def change_status():
    activity_type, text = next(status_cycle)
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=activity_type, name=text))

# ---------------- Dynamic Rainbow Embed ----------------
@tasks.loop(seconds=5)
async def update_embed_colors():
    for channel_id in list(channel_messages.keys()):
        category, msg, shift = channel_messages[channel_id]
        shift += 0.3  # ไล่สีต่อเนื่อง
        channel_messages[channel_id] = (category, msg, shift)
        try:
            embed = create_embed(category, shift)
            await msg.edit(embed=embed)
        except:
            continue

# ---------------- Run ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
