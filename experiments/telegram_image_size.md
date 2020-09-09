
This was an experiment to check maximum image size that can be sent via URL on telegram. And work out the limits.

## Results
So, using this script, I have found that:
- There is a maximum image semi-perimeter (width + height) of 10,000pixels.
- There is a maximum image aspect ratio of 1:20
- The switchover point between these is widths of 476-477 pixels.
  - Width 476 means height 9520, due to aspect ratio
  - Width 477 means height 9523, due to semi-perimeter


Swapping out the call() method in BeepFunctionality, for this:
```
    def call(self, update: Update, context: CallbackContext):
        logger.info("Beep")
        usage_logger.info("Beep function")

        message_text = update.message.text
        command = message_text.split()[0]
        args = message_text[len(command):].strip().split()
        if len(args) == 2:
            width = int(args[0])
            height = int(args[1])
            if not self.can_send_image(context, update, width, height):
                context.bot.send_message(chat_id=update.message.chat_id, text=f"Failed to send image {width}x{height}")
                print(f"Failed {width}x{height}")

            context.bot.send_message(chat_id=update.message.chat_id, text="boop")
        elif len(args) == 1:
            width = int(args[0])
            height_range = self.find_max_height_for_width(context, update, width)
            context.bot.send_message(chat_id=update.message.chat_id, text=f"For width {width} heights are {height_range}")
        else:
            width = 100
            height_range = self.find_max_height_for_width(context, update, width)
            context.bot.send_message(chat_id=update.message.chat_id, text=f"For width {width} heights are {height_range}")

    def find_max_height_for_width(self, context, update, width: int) -> Tuple[int, int]:
        max_aspect_ratio = 30
        max_semiperimeter = 11000
        height = min(int(width * max_aspect_ratio), max_semiperimeter-width)
        increments = 10 ** (len(str(height))-1)
        last_fail = None
        while True:
            if height > 0 and not self.can_send_image(context, update, width, height):
                last_fail = height
                height -= increments
            else:
                if increments == 1:
                    return last_fail, height
                height = last_fail
                increments //= 10

    def can_send_image(self, context, update, width: int, height: int) -> bool:
        print(f"Trying {width}x{height}")
        if width * height >= 16_000_000:
            url = f"https://source.unsplash.com/random/{width}x{height}.png"
        else:
            url = f"https://dummyimage.com/{width}x{height}.png"
        try:
            super(MQBot, context.bot).send_photo(
                chat_id=update.message.chat_id,
                photo=url
            )
            return True
        except telegram.error.BadRequest:
            return False

```