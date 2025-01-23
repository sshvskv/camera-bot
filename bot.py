import os
import pandas as pd
from datetime import datetime

from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from main import extract_frames, detect_objects
import time


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name} {update.effective_user.id}')

async def situation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    df = pd.read_csv(
        "./data/people_count.csv",
        names=['timestamp', 'value', 'filepath'],
        header=None,
        sep=',',
        parse_dates=['timestamp'])   
    
    working_hours = df[(df['timestamp'].dt.hour >= 9) & (df['timestamp'].dt.hour <= 18)] 
    last_timestamp = pd.to_datetime(df['timestamp']).max() # последний момент времени
    last_hour = last_timestamp - pd.Timedelta(hours=1) # последний час
    recent_data = df[df['timestamp'] >= last_hour.strftime('%Y-%m-%d %H:%M:%S')] # данные за последний час
    recent_data = recent_data.reset_index()

    last_week = last_timestamp - pd.Timedelta(days = 7) # последняя неделя
    working_hours = working_hours[working_hours['timestamp'] >= last_week.strftime('%Y-%m-%d %H:%M:%S')]

    recent_sum = recent_data['value'].sum()
    hourly_avg = int(working_hours.groupby(working_hours['timestamp'].dt.hour)['value'].sum().mean())

    num_days = working_hours['timestamp'].dt.date.nunique()
    hourly_avg_normalized = int(hourly_avg / num_days)

    print(working_hours.groupby(working_hours['timestamp'].dt.hour)['value'].sum())


    if recent_sum < hourly_avg_normalized: # если меньше от среднего
        status = "🟢"
    elif recent_sum < hourly_avg_normalized * 1.3: # если меньше среднего
        status = "🟡"
    else: # если больше среднего
        status = "🔴" 

    try:
        await update.message.reply_photo(
            photo=InputFile(
                obj=open("frames/result.jpg", 'rb'),
                filename="frame.jpg"),
                caption=f"Текущая ситуация на горе: {status}\n"
            f"Подъемов за последний час: {recent_sum}\n"
            f"Среднее число подъемов за час: {hourly_avg_normalized}"
        )
    except Exception as e:
        print(e)
        time.sleep(1)
        await update.message.reply_photo(
            photo=InputFile(
                obj=open("frames/result.jpg", 'rb'),
                filename="frame.jpg"),
                caption=f"Текущая ситуация на горе: {status}\n"
            f"Подъемов за последний час: {recent_sum}\n"
            f"Среднее число подъемов за час: {hourly_avg_normalized}"
        )
    finally:
        print("Message sent")

    # await app.bot.send_photo(chat_id=user,
    #             photo=InputFile(obj=image, filename="frame.jpg"),
    #             caption="Текущая ситуация на горе"
    #         )

async def monitor_web_cam(context):
    output_dir = "video_chunks"
    # массив названий видеофайлов
    videos = [file for file in os.listdir(output_dir) if ".mp4" in file]
    if len(videos) > 0: # если уже скачали видео
        filename = videos[0]
        extract_frames(filename, "./frames", 1) # достаем кадр из видео
        result = detect_objects("./frames/frame_1.jpg", 0.5) # распознаём объекты
        print(result)
        for user in [465999142, 96079551]: # отправляем нам сообщение с фото
            image = open("./frames/result.jpg", 'rb')
            await app.bot.send_photo(
                chat_id=user,
                photo=InputFile(obj=image, filename="frame.jpg"),
                caption="Текущая ситуация на горе"
            )
        for video in videos:
            os.remove(f"{output_dir}/{video}")
    else:
        for user in [465999142, 96079551]: # отправляем нам сообщение не найдены видео
            await app.bot.send_message(
                text="No videos found",
                chat_id=user,
            )


app = ApplicationBuilder().token("7766586491:AAEs4gzKwjGHzo5iNE-RPZ10DbdwG1mR8sI").build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("situation", situation))

if __name__ == "__main__":
    j = app.job_queue

    # job_low_balance = j.run_repeating(
    #     monitor_web_cam, # функция, которую мы выполняем 
    #     interval=10 # раз в 10 секунд
    # )
    app.run_polling(close_loop=False)
