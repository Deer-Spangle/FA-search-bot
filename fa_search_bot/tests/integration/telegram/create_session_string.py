import os

from pyrogram import Client

if __name__ == "__main__":
    client = Client(
        "pyrogram",
        api_id=os.getenv("CLIENT_API_ID"),
        api_hash=os.getenv("CLIENT_API_HASH"),
    )

    with client:
        print(client.export_session_string())
