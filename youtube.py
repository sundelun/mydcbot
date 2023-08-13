import youtube_dl
import discord
import asyncio


class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(cls.ytdl_format_options).extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else youtube_dl.YoutubeDL(cls.ytdl_format_options).prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), data=data)