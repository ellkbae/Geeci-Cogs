import discord
from PIL import Image,ImageFont,ImageDraw,ImageOps,ImageFilter
import aiohttp
from unidecode import unidecode
from io import BytesIO

class WelcomeC:
    def __init__(self,bot):
        self.bot = bot

    # im is the background to use (pass in from PIL's Image.open)
    # offset_x and offset_y refer to avatar img
    # returns BytesIO file-like object for easy use with bot.send_file
    async def welcome_member(self,im, font, member, offset_x=0, offset_y=-70,
                             new_width=1000, new_height=500, ava_sqdim=260,
                             text_offset_x=0, text_offset_y=140, text=None):
        im = im.copy()
        width, height = im.size

        name = unidecode(member.name)
        if text is None:
            welcome = 'Welcome {0},\n to {1.server.name}!'.format(name, member)
        else:
            welcome = text

        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = (width + new_width) // 2
        bottom = (height + new_height) // 2
        im = im.crop((left, top, right, bottom))

        # how to set up a gradient from the bottom:
        # fade_from = new_height/4
        # fade_to = new_height-fade_from
        #
        # fade_from = int(fade_from)
        # fade_to = int(fade_to)
        #
        # for i in range(fade_from, new_height+1):
        #     fade = int((i-fade_from)/(fade_to)*255)
        #     draw.rectangle(((0, i), (new_width, i)), fill=(0, 0, 0, fade))

        ov_left = 0
        ov_top = im.height // 2
        ov_right = im.width
        ov_bottom = im.height
        ov_box = (ov_left, ov_top, ov_right, ov_bottom)

        ov_ic = im.crop(ov_box)
        ov_ic = ov_ic.filter(ImageFilter.GaussianBlur(15))

        im.paste(ov_ic, ov_box)

        draw = ImageDraw.Draw(im, mode='RGBA')
        draw.rectangle(((ov_left, ov_top), (ov_right, ov_bottom)), fill=(0, 0, 0, 120))

        avatar_im = None
        url = member.avatar_url
        if not url:
            url = member.default_avatar_url

        async with aiohttp.ClientSession() as aiosession:
            with aiohttp.Timeout(10):
                async with aiosession.get(url) as resp:
                    avatar_im = BytesIO(await resp.read())

        resize = (ava_sqdim, ava_sqdim)
        avatar_im = Image.open(avatar_im).convert("RGBA")
        avatar_im = avatar_im.resize(resize, Image.ANTIALIAS)

        mask = Image.new('L', resize, 0)
        maskDraw = ImageDraw.Draw(mask)
        maskDraw.ellipse((0, 0) + resize, fill=255)
        mask = mask.resize(avatar_im.size, Image.ANTIALIAS)
        avatar_im.putalpha(mask)

        img_center_x = (im.width // 2)
        img_center_y = (im.height // 2)

        img_offset_x = img_center_x + offset_x
        img_offset_y = img_center_y + offset_y
        ava_right = img_offset_x + avatar_im.width//2
        ava_bottom = img_offset_y + avatar_im.height//2
        ava_left = img_offset_x - avatar_im.width//2
        ava_top = img_offset_y - avatar_im.height//2

        im.paste(avatar_im, box=(ava_left, ava_top, ava_right, ava_bottom), mask=avatar_im)

        text_width, text_height = draw.textsize(welcome, font=font)
        draw.text((((img_center_x - text_width / 2) + text_offset_x),
                   ((img_center_y - text_height / 2) + text_offset_y)),
                  welcome, fill='white', font=font, align='center')

        temp = BytesIO()
        im.save(temp, format='jpeg')
        temp.seek(0)

        return temp

    async def on_member_join(self,member):
        font = ImageFont.truetype("FORTE.ttf",70)
        # with open("pic.png","rb") as fp:
        im = Image.open("pic.ng")
        fp = await self.welcome_member(im,font,member)
        await self.bot.send_file(member.server,fp,filename = "welcome.jpg")


def setup(bot):
    bot.add_cog(WelcomeC(bot))
