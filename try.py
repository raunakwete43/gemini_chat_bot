import json


def get_chat_input(role):
    text = input(f"Enter {role} role chat: ")
    return {"role": role, "parts": [{"text": text}]}


def create_chat_history():
    chat_history = []

    # Get user role chat
    user_chat = get_chat_input("user")
    chat_history.append(user_chat)

    # Get model role chat
    model_chat = get_chat_input("model")
    chat_history.append(model_chat)

    return chat_history


def save_to_json(chat_history, filename):
    with open(filename, "w") as json_file:
        json.dump(chat_history, json_file, indent=2)


if __name__ == "__main__":
    chat_history = create_chat_history()

    # Specify the filename for the JSON file
    json_filename = "terminal_chat_history.json"

    # Save the chat history to a JSON file
    save_to_json(chat_history, json_filename)

    print(f"Chat history saved to {json_filename}")
