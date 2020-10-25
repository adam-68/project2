import win32clipboard
import json


def convert_to_dict():

    win32clipboard.OpenClipboard()
    tasks = win32clipboard.GetClipboardData().split("\r\n")
    win32clipboard.CloseClipboard()
    tasks_json = []

    for i in range(len(tasks)):
        row = tasks[i].split("\t")
        task = {
            "id": f"{i+1}".strip(),
            "sku": row[0].strip().lower(),
            "size": row[1].strip().replace(".", ","),
            "webhook_url": row[2].strip(),
            "bypass": row[3].strip().lower(),
            "product_url": row[4].strip()
        }
        tasks_json.append(task)

    with open("USER_INPUT_DATA/tasks.json", "w") as file:
        json.dump(tasks_json, file)


convert_to_dict()

