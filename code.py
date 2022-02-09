import alarm
import board
import displayio
import terminalio
import time
import adafruit_imageload
from adafruit_display_text import label
from secrets import secrets
from WiFiManager import WiFiManager

METRIC = False
BACKGROUND_BMP = "/bmps/weather_bg.bmp"
ICONS_LARGE_FILE = "/bmps/weather_icons_70px.bmp"
ICONS_SMALL_FILE = "/bmps/weather_icons_20px.bmp"
ICON_MAP = ("01", "02", "03", "04", "09", "10", "11", "13", "50")
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = ("January","February","March","April","May","June","July","August","September","October","November","December")
icons_large_bmp, icons_large_pal = adafruit_imageload.load(ICONS_LARGE_FILE)
icons_small_bmp, icons_small_pal = adafruit_imageload.load(ICONS_SMALL_FILE)
display = board.DISPLAY
wm = WiFiManager()

if (not alarm.wake_alarm is None and alarm.wake_alarm is alarm.pin.PinAlarm):
    print("PinAlarm value:")
    print(alarm.wake_alarm)
    print(alarm.wake_alarm.value)
    print(alarm.sleep_memory)

background = displayio.OnDiskBitmap(BACKGROUND_BMP)
group = displayio.Group()
bg_sprite = displayio.TileGrid(
    background,
    pixel_shader=background.pixel_shader,
    x=0,
    y=0,
)
group.append(bg_sprite)

def make_banner(data, x=0, y=0):
    day_of_week = label.Label(terminalio.FONT, text=DAYS[time.localtime(data["dt"]).tm_wday][:3].upper(), color=0x000000)
    day_of_week.anchor_point = (0, 0.5)
    day_of_week.anchored_position = (0, 10)
    icon = displayio.TileGrid(
        icons_small_bmp,
        pixel_shader=icons_small_pal,
        x=25,
        y=0,
        width=1,
        height=1,
        tile_width=20,
        tile_height=20,
    )
    icon[0] = ICON_MAP.index(data["weather"][0]["icon"][:2])
    day_temp = label.Label(terminalio.FONT, text=temperature_text(data["temp"]["day"]), color=0x000000)
    day_temp.anchor_point = (0, 0.5)
    day_temp.anchored_position = (50, 10)
    group = displayio.Group(x=x, y=y)
    group.append(day_of_week)
    group.append(icon)
    group.append(day_temp)
    return group

def temperature_text(tempK):
    if METRIC:
        return "{:3.0f}C".format(tempK - 273.15)
    else:
        return "{:3.0f}F".format(32.0 + 1.8 * (tempK - 273.15))

def wind_text(speedms):
    if METRIC:
        return "{:3.0f}m/s".format(speedms)
    else:
        return "{:3.0f}mph".format(2.23694 * speedms)

def go_to_sleep(current_time):
    hour, minutes, seconds = time.localtime(current_time)[3:6]
    seconds_since_midnight = 60 * (hour * 60 + minutes) + seconds
    seconds_to_sleep = (24 * 60 * 60 - seconds_since_midnight) + 15 * 60
    print(
        "Sleeping for {} hours, {} minutes".format(
            seconds_to_sleep // 3600, (seconds_to_sleep // 60) % 60
        )
    )
    alarms = []
    print("setting alarms")
    alarms.append(alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds_to_sleep))
    alarms.append(alarm.pin.PinAlarm(pin=board.BUTTON_A, value=0, pull=True))
    #alarms.append(alarm.pin.PinAlarm(pin=board.BUTTON_B, value=0, pull=True))
    #alarms.append(alarm.pin.PinAlarm(pin=board.BUTTON_C, value=0, pull=True))
    #alarms.append(alarm.pin.PinAlarm(pin=board.BUTTON_D, value=0, pull=True))
    print("sleeping")
    alarm.exit_and_deep_sleep_until_alarms(*alarms)

def drawScreen(forecast_data, utc_time, local_tz_offset):
    data = forecast_data[0]
    date = time.localtime(data["dt"])
    sunrise = time.localtime(data["sunrise"] + local_tz_offset)
    sunset = time.localtime(data["sunset"] + local_tz_offset)

    today_date = label.Label(terminalio.FONT, text="{} {} {}, {}".format(
        DAYS[date.tm_wday].upper(),
        MONTHS[date.tm_mon - 1].upper(),
        date.tm_mday,
        date.tm_year,
    ), color=0x000000)
    today_date.anchor_point = (0, 0)
    today_date.anchored_position = (15, 13)

    city_name = label.Label(
        terminalio.FONT, text=secrets["openweather_location"], color=0x000000
    )
    city_name.anchor_point = (0, 0)
    city_name.anchored_position = (15, 24)

    today_icon = displayio.TileGrid(
        icons_large_bmp,
        pixel_shader=icons_small_pal,
        x=10,
        y=40,
        width=1,
        height=1,
        tile_width=70,
        tile_height=70,
    )
    today_icon[0] = ICON_MAP.index(data["weather"][0]["icon"][:2])

    today_morn_temp = label.Label(terminalio.FONT, text=temperature_text(data["temp"]["morn"]), color=0x000000)
    today_morn_temp.anchor_point = (0.5, 0)
    today_morn_temp.anchored_position = (118, 59)

    today_day_temp = label.Label(terminalio.FONT, text=temperature_text(data["temp"]["day"]), color=0x000000)
    today_day_temp.anchor_point = (0.5, 0)
    today_day_temp.anchored_position = (149, 59)

    today_night_temp = label.Label(terminalio.FONT, text=temperature_text(data["temp"]["night"]), color=0x000000)
    today_night_temp.anchor_point = (0.5, 0)
    today_night_temp.anchored_position = (180, 59)

    today_humidity = label.Label(terminalio.FONT, text="{:3d}%".format(data["humidity"]), color=0x000000)
    today_humidity.anchor_point = (0, 0.5)
    today_humidity.anchored_position = (105, 95)

    today_wind = label.Label(terminalio.FONT, text=wind_text(data["wind_speed"]), color=0x000000)
    today_wind.anchor_point = (0, 0.5)
    today_wind.anchored_position = (155, 95)

    today_sunrise = label.Label(terminalio.FONT, text="{:2d}:{:02d} AM".format(sunrise.tm_hour, sunrise.tm_min), color=0x000000)
    today_sunrise.anchor_point = (0, 0.5)
    today_sunrise.anchored_position = (45, 117)

    today_sunset = label.Label(terminalio.FONT, text="{:2d}:{:02d} PM".format(sunset.tm_hour - 12, sunset.tm_min), color=0x000000)
    today_sunset.anchor_point = (0, 0.5)
    today_sunset.anchored_position = (130, 117)

    today_banner = displayio.Group()
    today_banner.append(today_date)
    today_banner.append(city_name)
    today_banner.append(today_icon)
    today_banner.append(today_morn_temp)
    today_banner.append(today_day_temp)
    today_banner.append(today_night_temp)
    today_banner.append(today_humidity)
    today_banner.append(today_wind)
    today_banner.append(today_sunrise)
    today_banner.append(today_sunset)

    future_banners = [
        make_banner(forecast_data[1], x=210, y=18),
        make_banner(forecast_data[2], x=210, y=39),
        make_banner(forecast_data[3], x=210, y=60),
        make_banner(forecast_data[4], x=210, y=81),
        make_banner(forecast_data[5], x=210, y=102)
    ]

    group.append(today_banner)
    for future_banner in future_banners:
        group.append(future_banner)

# ===========
#  M A I N
# ===========
latlon = wm.get_latlon()
forecast_data, utc_time, local_tz_offset = wm.get_forecast(latlon)
drawScreen(forecast_data, utc_time, local_tz_offset)

print("Refreshing...")
time.sleep(display.time_to_refresh + 1)
display.show(group)
display.refresh()
time.sleep(display.time_to_refresh + 1)
go_to_sleep(utc_time + local_tz_offset)

