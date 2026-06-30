import asyncio
from config import config

async def health_server():
    async def handle(reader, writer):
        await reader.read(1024)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        await writer.drain()
        writer.close()
        
    server = await asyncio.start_server(handle, "0.0.0.0", config.PORT)
    async with server:
        await server.serve_forever()
