import pytest
import sys

from telebot import types

sys.path.insert(0, "../dff-generics")

from dff_telegram_connector.types import (
    TelegramImage,
    TelegramGallery,
    TelegramAudio,
    TelegramVideo,
    TelegramDocument,
    TelegramResponse,
)
from dff_generics import Image, Video, Audio, Document, Attachments, Response


@pytest.mark.parametrize(
    "Local,Generic,Adapter,value",
    [
        (types.InputMediaPhoto, Image, TelegramImage, "file.jpg"),
        (types.InputMediaAudio, Audio, TelegramAudio, "file.mp3"),
        (types.InputMediaDocument, Document, TelegramDocument, "file.txt"),
        (types.InputMediaVideo, Video, TelegramVideo, "file.mp4"),
    ],
)
def test_adapt_media(Local, Generic, Adapter, value):
    local = Local(media=value, caption=value)
    generic = Generic(source=value, title=value)
    parsed_local = Adapter.parse_obj(local)
    parsed_generic = Adapter.parse_obj(generic)
    assert parsed_local == parsed_generic
    assert parsed_local.to_local() == local
    assert parsed_generic.to_local() == local


def test_adapt_response():
    response = Response(text="A quick brown fox")
    assert response
    adapted_response = TelegramResponse.parse_obj(response)
    assert adapted_response and adapted_response.text == "A quick brown fox"


def test_adapt_video_gallery():
    videos = ["https://youtu.be/QH2-TGUlwu4"] * 10
    vid_list = [Video(source=item) for item in videos]
    response = Response(text="video gallery", gallery=Attachments(files=vid_list))
    assert response
    adapted_response = TelegramResponse[TelegramVideo].parse_obj(response)
    assert adapted_response and adapted_response.text == "video gallery"


def test_adapt_photo_gallery():
    pics = ["examples/pictures/kitten.jpg"] * 10
    pic_list = [Image(source=item) for item in pics]
    response = Response(text="pic gallery", gallery=Attachments(files=pic_list))
    assert response
    adapted_response = TelegramResponse[TelegramImage].parse_obj(response)
    assert adapted_response and adapted_response.text == "pic gallery"
