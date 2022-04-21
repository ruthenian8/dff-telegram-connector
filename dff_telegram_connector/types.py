from ctypes import Union
from typing import List, Optional, Generic, TypeVar
from wsgiref.validate import validator

from telebot import TeleBot, types
from pydantic import BaseModel, Field, Extra, FilePath, HttpUrl
from pydantic.generics import GenericModel

try:
    import dff_generics
except (ImportError, ModuleNotFoundError):
    dff_generics = None


MediaType = TypeVar("MediaType")


class AdapterModel(BaseModel):
    class Config:
        extra = Extra.ignore
        allow_population_by_field_name = True


class TelegramButton(AdapterModel):
    text: str = Field(alias="title")
    url: Optional[str] = Field(default=None, alias="url")
    callback_data: Optional[dict] = Field(default=None, alias="payload")

    @property
    def InlineKeyboardButton(self):
        return types.InlineKeyboardButton(**self.dict())

    @property
    def KeyboardButton(self):
        return types.KeyboardButton(text=self.text)


class TelegramUI(AdapterModel):
    buttons: Optional[List[TelegramButton]] = None
    is_inline: bool = True
    keyboard: Optional[Union[types.ReplyKeyboardRemove, types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup]] = None
    row_width: int = 3

    def __init__(self, *, buttons=None, is_inline=False, keyboard=None, row_width=3):
        if keyboard and isinstance(keyboard, types.ReplyKeyboardRemove):
            super(TelegramUI, self).__init__(keyboard=keyboard, row_width=row_width)
            return

        if not buttons:
            raise ValueError(
                "`Buttons` parameter is required, when `keyboard` is not equal to telebot.types.ReplyKeyboardRemove."
            )

        if is_inline:
            keyboard = types.InlineKeyboardMarkup([item.InlineKeyboardButton for item in buttons], row_width=row_width)
            super(TelegramUI, self).__init__(buttons=buttons, keyboard=keyboard, row_width=row_width)
            return

        keyboard = types.ReplyKeyboardMarkup(row_width=row_width)
        buttons = [item.KeyboardButton for item in buttons]
        for idx in range(0, len(buttons), row_width):
            keyboard.row(buttons[idx, idx + row_width])
        super(TelegramUI, self).__init__(buttons=buttons, keyboard=keyboard, row_width=row_width)


class TelegramResource(AdapterModel):
    caption: Optional[str] = Field(default=None, alias="title")
    media: Union[FilePath, HttpUrl] = Field(alias="source")


class TelegramImage(TelegramResource):
    _bot_method: str = Field(default="send_photo", const=True)

    def to_local(self):
        return types.InputMediaPhoto(**self.dict())


class TelegramAudio(TelegramResource):
    _bot_method: str = Field(default="send_audio", const=True)

    def to_local(self):
        return types.InputMediaAudio(**self.dict())


class TelegramVideo(TelegramResource):
    _bot_method: str = Field(default="send_video", const=True)

    def to_local(self):
        return types.InputMediaVideo(**self.dict())


class TelegramDocument(TelegramResource):
    _bot_method: str = Field(default="send_video", const=True)

    def to_local(self):
        return types.InputMediaDocument(**self.dict())


class TelegramGallery(GenericModel, Generic[MediaType]):
    files: List[MediaType] = Field(default_factory=list, min_items=2, max_items=10)

    def to_local(self):
        return [item.to_local() for item in self.files]


class TelegramResponse(GenericModel, Generic[MediaType]):
    text: str = ...
    ui: Optional[TelegramUI] = None
    document: Optional[TelegramDocument] = None
    image: Optional[TelegramImage] = None
    video: Optional[TelegramVideo] = None
    audio: Optional[TelegramAudio] = None
    gallery: Optional[TelegramGallery[MediaType]] = None
