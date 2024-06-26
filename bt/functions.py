import os, json
from aiogram.types import FSInputFile
from aiogram import types, Bot
from data import config
from openai import AsyncOpenAI
from db.db_init import init_bd
from db.db_functions import update_user_values


client = AsyncOpenAI(api_key=config.openai_api_token)
bot = Bot(token=config.bot_token)
value_determiner_id = "asst_JP40uNAluP87Ph6s6ML1t22O"
assistant_id = "asst_O1WZMPnShmNbXCbER8oThP8K"


async def answer_voice(message: types.Message):
    chat_id = message.from_user.id
    ivoice_path = f"voice_cache/ivoice_{str(chat_id)}.ogg"
    await download_voice(message, ivoice_path)
    transcription_model = "whisper-1"
    transcription = await get_transcription(ivoice_path, transcription_model)
    role = get_role("user")
    assistant_model = "gpt-4o"
    text_answer = await get_answer(transcription, role, assistant_model, assistant_id)
    ovoice_path = f"voice_cache/ovoice_{str(chat_id)}.ogg"
    voice_over_model = "tts-1"
    voice_model = get_voice_model("alloy")
    await voice_over(text_answer, ovoice_path, voice_over_model, voice_model)
    await send_voice(message, ovoice_path)
    clear_cache([ivoice_path, ovoice_path])


async def determine_values(message: types.Message):
    ivoice_path = "voice_cache/ivoice.ogg"
    await download_voice(message, ivoice_path)
    transcription_model = "whisper-1"
    transcription = await get_transcription(ivoice_path, transcription_model)
    values = await determine_values_in_text(transcription)
    if await validate_values(values):
        await init_bd()
        await update_user_values(message.from_user.id, values)


async def validate_values(values: str) -> bool:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Ты должен четко следовать инструкциям. Давать ответ в полном соответствии с форматом."
            },
            {
                "role": "user",
                "content": values
            }

        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "valid_values",
                    "description": "Я попытался выделить ключевые ценности пользователя. Тебе нужно определить, являются ли они осмысленными и правильными. Ответ типа bool, 'True' — являются, 'False' — не являются.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "values": {
                                "type": "string",
                                "description": "Выделенные ценности"
                            }
                        },
                        "required": ["values"]
                    }
                }
            }
        ],
        tool_choice="required",
    )
    tool = response.choices[0].message.tool_calls[0]
    is_valid = json.loads(tool.function.arguments)["values"]
    return is_valid


async def determine_values_in_text(text: str):
    thread = await client.beta.threads.create()
    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )

    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=value_determiner_id,
    )
    tool_outputs = ""
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        tool_outputs += messages.data[0].content[0].text.value + " "

    if run.status == "requires_action":
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            tool_outputs += json.loads(tool.function.arguments)["text"] + " "

    return tool_outputs


async def download_voice(message: types.Message, ivoice_path: str):
    voice_id = message.voice.file_id
    voice_file = await bot.get_file(voice_id)
    voice_file_path = voice_file.file_path
    await bot.download_file(voice_file_path, ivoice_path)


async def get_transcription(ivoice_path: str, model: str):
    with open(ivoice_path, "rb") as audio_file:
        transcription = await client.audio.transcriptions.create(model=model, file=audio_file, response_format="text")
    return transcription


async def get_answer(transcription: str, role, model: str, assistant_id:str) -> str:
    thread = await client.beta.threads.create()
    await client.beta.threads.messages.create(thread_id=thread.id, role=role, content=transcription)
    run = await client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant_id)
    if run.status == "completed":
        messages = await client.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value
    return answer


async def voice_over(text_input: str, path: str, voice_over_model: str, voice_model):
    response = await client.audio.speech.create(model=voice_over_model, voice=voice_model, input=text_input)
    response.stream_to_file(path)


async def send_voice(message: types.Message, path: str):
    vc = FSInputFile(path)
    await message.answer_voice(vc)


def get_role(role: str):
    if role in ["user", "assistant"]:
        return role
    else:
        raise ValueError


def get_voice_model(model: str):
    if model in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        return model
    else:
        raise ValueError


def clear_cache(path_list: list[str]):
    for path in path_list:
        os.remove(path)
