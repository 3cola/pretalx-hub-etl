from datetime import datetime
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

# Some settings
SOURCE_SCHEDULE_JSON_URL = "https://pretalx.riat.at/38c3/schedule/widgets/schedule.json"

TARGET_SCHEME = "http"
TARGET_HOST = "localhost"
# TODO: do not use an ID here, use a slug, the resolve the id with the target Hub API based on the slug
ASSEMBLY_ID = "cf9df612-3222-4675-91df-62c720763cdd"
TARGET_URL_LOGIN = TARGET_SCHEME + "://" + TARGET_HOST + "/accounts/login/"
TARGET_URL_ASSEMBLY_NEW_EVENT = (
    TARGET_SCHEME
    + "://"
    + TARGET_HOST
    + "/backoffice/assembly/"
    + ASSEMBLY_ID
    + "/new_event"
)


# Some mapping tables
MAP_ROOMS = {
    1: "CDC Mini Stage",
    2: "CDC Pentagon",
    3: "CDC Circle",
}


# Extract
response = requests.get(SOURCE_SCHEDULE_JSON_URL)
source_schedule = response.json()
print(json.dumps(source_schedule, indent=4))

# TODO: extract the list of events form the HUB target API


# Transform
events = []
talks = source_schedule["talks"]
for talk in talks:
    event = {}
    event["name"] = talk["title"] or ""
    event["location"] = "CDC"
    # here we need a mapping table and solve the roomId
    event["room"] = MAP_ROOMS[talk["room"]] or ""
    event["language"] = "en"
    event["abstract"] = talk["abstract"] or ""
    event["description_de"] = ""
    event["description_en"] = ""
    event["schedule_start"] = datetime.strptime(talk["start"], "%Y-%m-%dT%H:%M:%S%z")
    event["duration"] = talk["duration"]
    # space delimited words
    # I use the tag to store the pretalx talk code
    event["tags"] = talk["code"] or ""
    events.append(event)

print(events)

# TODO: compare the event list from the target and the source to know which event needs to be updated,
# or created or deleted, add an operation flag in the event object (create/delete/update)


# Load

driver = webdriver.Firefox()
# Login
driver.get(TARGET_URL_LOGIN)
driver.find_element(By.NAME, "login").send_keys("admin")
driver.find_element(By.NAME, "password").send_keys("admin")
driver.find_element(
    By.XPATH,
    "/html/body/div[1]/div/div/div/div/div/form/div[2]/button",
).click()

# TODO: base on the operation flag of the event object, wither we delete, update or create the event
# create new events
for event in events:
    driver.get(TARGET_URL_ASSEMBLY_NEW_EVENT)
    select_room = Select(driver.find_element(By.NAME, "room"))
    select_room.select_by_visible_text(event["room"])
    driver.find_element(By.NAME, "location").send_keys(event["location"])
    driver.find_element(By.NAME, "name").send_keys(event["name"])
    select_language = Select(driver.find_element(By.ID, "id_language"))
    select_language.select_by_visible_text(event["language"])
    driver.find_element(By.NAME, "abstract").send_keys(event["abstract"])
    driver.find_element(By.NAME, "description_de").send_keys(event["description_de"])
    driver.find_element(By.NAME, "description_en").send_keys(event["description_en"])
    datetime_start = driver.find_element(By.NAME, "schedule_start")
    datetime_start.send_keys(event["schedule_start"].month)
    datetime_start.send_keys(event["schedule_start"].day)
    datetime_start.send_keys(event["schedule_start"].year)
    datetime_start.send_keys(event["schedule_start"].hour)
    datetime_start.send_keys(event["schedule_start"].minute)
    driver.find_element(By.NAME, "schedule_duration").send_keys(event["duration"])
    driver.find_element(By.NAME, "tags_list").send_keys(event["duration"])
    driver.find_element(By.ID, "eventForm").submit()

    # TODO: driver wait and check the form validation for any error

# TODO: implement the code to delete an event
# TODO: implement the code to update an event

# driver.quit()

# TODO: pull again the list of events form the target Hub API
# and compare it to our events object to check for good completion

# TODO: error management
