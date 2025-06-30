from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message

# -----------------------------
# CONFIG
# -----------------------------
API_ID = 29568441
API_HASH = "b32ec0fb66d22da6f77d355fbace4f2a"
BOT_TOKEN = "7664057329:AAGH1pOPZxv2EQpkdxM_esVlbu8u-R8Z5Ng"

# -----------------------------
# 1. Load DialoGPT-small
# -----------------------------
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

# -----------------------------
# 2. In-memory chat histories
# -----------------------------
chat_histories = {}  # chat_id -> torch.Tensor of token IDs

EMOJIS = ["😎", "😂", "🤖", "🔥", "👍", "💥"]

# -----------------------------
# 3. Build Pyrogram client
# -----------------------------
app = Client(
    "dumb_chat_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# -----------------------------
# 4. Handlers
# -----------------------------
@app.on_message(filters.command("start"))
def start_cmd(client: Client, message: Message):
    message.reply_text(
        "👋 Hey bro! I'm your dumb vibing bot.\n"
        "Just send me any text and I'll reply token-by-token!"
    )

@app.on_message(filters.command("reset"))
def reset_cmd(client: Client, message: Message):
    chat_histories.pop(message.chat.id, None)
    message.reply_text("🔄 Chat history cleared. Let's start fresh!")

@app.on_message(filters.text & ~filters.command(["start", "reset"]))
def handle_message(client: Client, message: Message):
    chat_id = message.chat.id
    user_text = message.text

    # Append user message to history
    new_ids = tokenizer.encode(user_text + tokenizer.eos_token, return_tensors="pt")
    if chat_id in chat_histories:
        input_ids = torch.cat([chat_histories[chat_id], new_ids], dim=-1)
    else:
        input_ids = new_ids

    sent = message.reply_text("⏳ thinking...")

    # Generate reply
    output = model.generate(
        input_ids,
        max_length=input_ids.shape[-1] + 100,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.75,
        output_scores=True,
        return_dict_in_generate=True
    )
    reply_ids = output.sequences[:, input_ids.shape[-1]:][0]

    partial = ""
    flush_interval = 5  # Edit every 5 tokens (adjust as needed)
    token_count = 0

    for token_id in reply_ids:
        token = tokenizer.decode(token_id, skip_special_tokens=True)
        partial += token
        token_count += 1

        if token_count % flush_interval == 0:
            try:
                sent.edit_text(partial + " ✍️")
            except Exception:
                pass

        time.sleep(0.03)

    # Final edit
    final = partial + " " + random.choice(EMOJIS)
    try:
        sent.edit_text(final)
    except Exception:
        pass

    chat_histories[chat_id] = input_ids[:, -1000:]

# -----------------------------
# 5. Run
# -----------------------------
if __name__ == "__main__":
    app.run()
