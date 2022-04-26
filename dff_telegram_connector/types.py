"""
Types
******

This module implements  
"""
from typing import Any, List, Optional, Union
from pathlib import Path

from telebot import types
from pydantic import BaseModel, ValidationError, validator, root_validator, Field, Extra, FilePath, HttpUrl

try:
    import dff_generics
except (ImportError, ModuleNotFoundError):
    dff_generics = None


class AdapterModel(BaseModel):
    class Config:
        extra = Extra.ignore
        allow_population_by_field_name = True


class TelegramButton(AdapterModel):
    text: str = Field(alias="text")
    url: Optional[str] = Field(default=None, alias="source")
    callback_data: Optional[dict] = Field(default=None, alias="payload")


class TelegramUI(AdapterModel):
    buttons: Optional[List[TelegramButton]] = None
    is_inline: bool = True
    keyboard: Optional[Union[types.ReplyKeyboardRemove, types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup]] = None
    row_width: int = 3

    @root_validator
    def init_validator(cls, values: dict):
        if isinstance(values["keyboard"], types.ReplyKeyboardRemove):  # no changes if buttons are not required
            return values
        if not values.get("buttons"):
            raise ValueError(
                "`buttons` parameter is required, when `keyboard` is not equal to telebot.types.ReplyKeyboardRemove."
            )
        kb_args = {"row_width": values.get("row_width")}
        is_inline = values.get("is_inline")
        if is_inline:
            keyboard = types.InlineKeyboardMarkup(**kb_args)
            buttons = [types.InlineKeyboardButton(**item.dict()) for item in values["buttons"]]
        else:
            keyboard = types.ReplyKeyboardMarkup(**kb_args)
            buttons = [types.KeyboardButton(text=item.text) for item in values["buttons"]]
        keyboard.add(buttons, row_width=values["row_width"])
        values["keyboard"] = keyboard
        return values


class TelegramAttachment(BaseModel):
    source: Optional[Union[HttpUrl, FilePath]] = None
    id: Optional[str] = None  # id field is made separate to simplify validation.
    title: Optional[str] = None

    @root_validator
    def validate_id_or_source(cls, values):
        if bool(values["source"]) == bool(values["id"]):
            raise ValidationError("Attachment type requires exactly one parameter, `source` or `id`, to be set.")
        return values

    @validator("source", pre=False)
    def validate_source(cls, source: Optional[Union[HttpUrl, FilePath]]):
        if not isinstance(source, Path):
            return source
        if not source.exists():
            raise ValidationError(f"Provided filepath {str(source)} does not exist")
        return source


class TelegramAttachments(BaseModel):
    files: List[types.InputMedia] = Field(default_factory=list, min_items=2, max_items=10)

    @validator("files", pre=True, each_item=True, always=True)
    def cast_to_input_media(cls, file: Any):
        tg_cls = None

        if dff_generics:  # convert generic classes to the corresponding InputMedia classes
            if isinstance(file, dff_generics.Image):
                tg_cls = types.InputMediaPhoto
            elif isinstance(file, dff_generics.Audio):
                tg_cls = types.InputMediaAudio
            elif isinstance(file, dff_generics.Document):
                tg_cls = types.InputMediaDocument
            elif isinstance(file, dff_generics.Video):
                tg_cls = types.InputMediaVideo

        if tg_cls:
            file = tg_cls(media=file.source or file.id, caption=file.title)

        if isinstance(file, types.InputMedia):
            return file
        else:
            raise TypeError(
                """`files` field can only hold InputMedia objects (pytelegrambotapi lib), 
                or Image, Video, Audio or Document objects (dff_generics lib).
                """
            )


class TelegramResponse(BaseModel):
    text: str = ...
    ui: Optional[TelegramUI] = None
    location: Optional[types.Location] = None
    document: Optional[TelegramAttachment] = None
    image: Optional[TelegramAttachment] = None
    video: Optional[TelegramAttachment] = None
    audio: Optional[TelegramAttachment] = None
    attachments: Optional[TelegramAttachments] = None
