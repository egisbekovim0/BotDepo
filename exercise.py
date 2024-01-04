import logging
from typing import Dict
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE, REQUEST_CONTACT = range(4)

reply_keyboard = [
    ["Push ups", "Squats"],
    ["Crunches", "Something else..."],
    ["Done", "Send number"],
]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

async def start_place_order(update: Update, context: CallbackContext) -> int:
    """Start the place order process."""
    keyboard = [
        [KeyboardButton(text="My phone number", request_contact=True)],
        ["Cancel"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "How can we contact you?",
        reply_markup=reply_markup,
    )

    return REQUEST_CONTACT

async def handle_contact(update: Update, context: CallbackContext) -> int:
    """Handle the received contact information."""
    contact_info = update.message.contact
    user_data = context.user_data
    user_data["telephone"] = contact_info.phone_number 

    
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"Thank you {contact_info.first_name} with phone {contact_info.phone_number}!",
        reply_markup=reply_markup,
    )

    return CHOOSING

def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(
        "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
        "Why don't you tell me something about yourself?",
        reply_markup=markup,
    )

    return CHOOSING

async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Your {text.lower()}? Yes, I would love to hear about that!")

    return TYPING_REPLY

async def custom_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for a description of a custom category."""
    await update.message.reply_text(
        'Alright, please send me the category first, for example "Most impressive skill"'
    )

    return TYPING_CHOICE

async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = int(update.message.text)
    category = user_data["choice"]

    user_data.setdefault(category, 0)
    user_data[category] += text



    await update.message.reply_text(
        f"Neat! You've done a total of {user_data[category]} {category.lower()}!"
        f"{facts_to_str(user_data)}",
        reply_markup=markup,
    )

    return CHOOSING

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    await update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(user_data)}Until next time!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6730041729:AAG8pSQREE-TugDQCsPlioeF1dtoVaQgctY").build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Push ups|Squats|Crunches)$"), regular_choice
                ),
                MessageHandler(
                    filters.Regex("^Send number$"), start_place_order
                ),
                MessageHandler(filters.Regex("^Something else...$"), custom_choice),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                    received_information,
                )
            ],
            REQUEST_CONTACT: [MessageHandler(filters.CONTACT, handle_contact)]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()