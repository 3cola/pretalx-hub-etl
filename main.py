from datetime import datetime
from time import sleep
from os import wait
from pprint import pprint
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from settings import (
    MAP_ROOMS,
    SOURCE_SCHEDULE_JSON_URL,
    AUTO_PUBLISH,
    AUTO_DELETE_EVENTS,
    INTERACTIVE,
    TARGET_API_TOKEN,
    TARGET_HTTP_LOGIN,
    TARGET_HTTP_PASSWORD,
    TARGET_HTTP_PART1,
    TARGET_API_PART1,
    TARGET_API_PART2,
    ASSEMBLY_SLUG,
)

# Setting up constants
TARGET_URL_API_ASSEMBLIES = TARGET_API_PART1 + TARGET_API_PART2 + "assemblies/"
TARGET_URL_API_EVENTS = TARGET_API_PART1 + TARGET_API_PART2 + "events/"

# get the ASSEMBLY_ID
API_HEADERS = {"Authorization": "Bearer " + TARGET_API_TOKEN, "Accept": "json"}
# print(API_HEADERS)
query_params = {"slug": ASSEMBLY_SLUG}
response = requests.get(
    url=TARGET_URL_API_ASSEMBLIES, headers=API_HEADERS, params=query_params
)
print(response)
response_json = response.json()
if len(response_json["data"]) == 0:
    print(response_json)

ASSEMBLY_ID = response_json["data"][0]["id"]
print("Assembly id : " + ASSEMBLY_ID)
if not ASSEMBLY_ID:
    raise Exception(
        "The assembly with slug "
        + ASSEMBLY_SLUG
        + " does not exists. You should create it first."
    )

TARGET_URL_LOGIN = TARGET_HTTP_PART1 + "/accounts/login/"
TARGET_URL_ASSEMBLY_NEW_EVENT = (
    TARGET_HTTP_PART1 + "/backoffice/assembly/" + ASSEMBLY_ID + "/new_event"
)
TARGET_URL_ASSEMBLY_UPDATE_EVENT = (
    TARGET_HTTP_PART1 + "/backoffice/assembly/" + ASSEMBLY_ID + "/e/"
)


# Some function
def get_target_events(ASSEMBLY_ID, TARGET_URL_API_EVENTS, API_HEADERS):
    # extract the list of events from the target api
    query_params = {"assemblyID": ASSEMBLY_ID, "pageSize": 100, "page": 1}
    response = requests.get(
        url=TARGET_URL_API_EVENTS, headers=API_HEADERS, params=query_params
    )
    # print(response)
    response_json = response.json()
    # print(response_json)
    target_events = []
    if len(response_json["data"]) > 0:
        target_events.extend(response_json["data"])
    total = response_json["pagination"]["total"]
    page = response_json["pagination"]["page"]
    page_size = response_json["pagination"]["page_size"]
    more = True if total > page * page_size else False
    while more:
        query_params["page"] = query_params["page"] + 1
        response = requests.get(
            url=TARGET_URL_API_EVENTS, headers=API_HEADERS, params=query_params
        )
        # print(response)
        response_json = response.json()
        # print(response_json)
        if len(response_json["data"]) > 0:
            target_events.extend(response_json["data"])
        total = response_json["pagination"]["total"]
        page = response_json["pagination"]["page"]
        page_size = response_json["pagination"]["page_size"]
        more = True if total > page * page_size else False
    return target_events


# Extract

# get the source data
response = requests.get(SOURCE_SCHEDULE_JSON_URL)
source_schedule = response.json()
# print(json.dumps(source_schedule, indent=4))

target_events = get_target_events(ASSEMBLY_ID, TARGET_URL_API_EVENTS, API_HEADERS)
# print("target_events")
# pprint(target_events)


# Transform

speaker_map = {}
speakers = source_schedule["speakers"]
for speaker in speakers:
    speaker_map[speaker["code"]] = speaker["name"]

events = []
talks = source_schedule["talks"]
for talk in talks:
    event = {}
    event["name"] = talk["title"] or ""
    # TODO: check what to put in the location...
    event["location"] = "CDC"
    # here we need a mapping table and solve the roomId
    event["room"] = MAP_ROOMS[talk["room"]] or ""
    event["language"] = "en"
    event["abstract"] = talk["abstract"] or ""
    event["speakers"] = list(map(lambda x: speaker_map[x], talk["speakers"]))
    event["description_de"] = ""
    event["description_en"] = "Speaker{}: {}".format(
        "" if len(event["speakers"]) == 1 else "s", ", ".join(event["speakers"])
    )
    event["schedule_start"] = datetime.strptime(talk["start"], "%Y-%m-%dT%H:%M:%S%z")
    event["duration"] = talk["duration"]
    # space delimited words ?
    # I use the tag to store the pretalx talk code
    event["tags"] = talk["code"] or ""
    # check if the event exists on the target to decide if we create it or update it
    op_flag = "create"
    etag = event["tags"].lower()
    for te in target_events:
        tetags = te["tags"][0].lower()

        if tetags == etag:
            op_flag = "update"
            event["id"] = te["id"]
            break
    event["op_flag"] = op_flag
    events.append(event)

print("events " + str(len(events)))
# pprint(events)

# check events that dont exist / have been deleted from source, so we can delete them in the target
events_to_delete = []
for te in target_events:
    tetags = te["tags"][0].lower()
    exists = False
    for event in events:
        etag = event["tags"].lower()
        if tetags == etag:
            exists = True
    if exists == False:
        event = {}
        event["id"] = te["id"]
        event["name"] = te["name"]
        event["op_flag"] = "delete"
        events_to_delete.append(event)

print("events_to_delete " + str(len(events_to_delete)))
# pprint(events_to_delete)


# Load

driver = webdriver.Firefox()
# Login
driver.get(TARGET_URL_LOGIN)
driver.find_element(By.NAME, "login").send_keys(TARGET_HTTP_LOGIN)
driver.find_element(By.NAME, "password").send_keys(TARGET_HTTP_PASSWORD)
driver.find_element(
    By.XPATH, "/html/body/div[1]/div/div/div/div/div/form/div[2]/button"
).click()
sleep(1)

# delete events
if AUTO_DELETE_EVENTS == True:
    for event in events_to_delete:
        if event["op_flag"] == "delete":
            print("delete " + event["name"])
            driver.get(TARGET_URL_ASSEMBLY_UPDATE_EVENT + event["id"])
            driver.find_element(By.ID, "EventDeleteForm").submit()
            sleep(1)


# create or update events
for event in events:
    url = ""
    match event["op_flag"]:
        case "create":
            url = TARGET_URL_ASSEMBLY_NEW_EVENT
            print("create " + event["name"])
        case "update":
            url = TARGET_URL_ASSEMBLY_UPDATE_EVENT + event["id"]
            print("update " + event["name"])
        case _:
            print("Unknown op_flag : " + event["op_flag"])
            pprint(event)
            break
    driver.get(url)
    select_room = Select(driver.find_element(By.NAME, "room"))
    select_room.select_by_visible_text(event["room"])
    driver.find_element(By.NAME, "location").clear()
    driver.find_element(By.NAME, "location").send_keys(event["location"])
    driver.find_element(By.NAME, "name").clear()
    driver.find_element(By.NAME, "name").send_keys(event["name"])
    select_language = Select(driver.find_element(By.ID, "id_language"))
    select_language.select_by_visible_text(event["language"])
    driver.find_element(By.NAME, "abstract").clear()
    driver.find_element(By.NAME, "abstract").send_keys(event["abstract"])
    driver.find_element(By.NAME, "description_de").clear()
    driver.find_element(By.NAME, "description_de").send_keys(event["description_de"])
    driver.find_element(By.NAME, "description_en").clear()
    driver.find_element(By.NAME, "description_en").send_keys(event["description_en"])
    datetime_start = driver.find_element(By.NAME, "schedule_start")
    datetime_start.send_keys(event["schedule_start"].month)
    datetime_start.send_keys(event["schedule_start"].day)
    datetime_start.send_keys(event["schedule_start"].year)
    datetime_start.send_keys(event["schedule_start"].hour)
    datetime_start.send_keys(event["schedule_start"].minute)
    driver.find_element(By.NAME, "schedule_duration").clear()
    driver.find_element(By.NAME, "schedule_duration").send_keys(event["duration"])
    driver.find_element(By.NAME, "tags_list").clear()
    driver.find_element(By.NAME, "tags_list").send_keys(event["tags"])
    driver.find_element(By.ID, "eventForm").submit()
    # wait few seconds, the element with id messages may take a delay to appear
    sleep(2)
    # check for invalid
    messages_html = None
    try:
        messages_element = driver.find_element(By.ID, "messages")
        messages_html = messages_element.get_attribute("innerHTML") or ""
    except Exception as e:
        print("element with id 'messages' was not found")
        print(e)

    is_invalid = (
        True if messages_html and messages_html.lower().find("invalid") > 0 else False
    )
    if is_invalid:
        # The submission on the form failed, the update or create was not successful
        print("Invalid form submit : " + event["op_flag"] + " " + event["name"])
        sleep(1)
        if INTERACTIVE:
            input("Fix the invalid form, then Press Enter to continue...")
    if AUTO_PUBLISH and not is_invalid:
        publish_button = driver.find_element(By.ID, "publishEvent")
        if publish_button.text == "Event__publish__submit":
            publish_button.click()
            sleep(1)
            driver.find_element(By.ID, "confirmationModalSubmit").click()

# wait few seconds and quit
sleep(2)
driver.quit()
