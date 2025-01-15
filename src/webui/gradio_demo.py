"""基于gradio构建的一个简洁的交互式的聊天机器人 Web 界面"""
import gradio as gr


css = """
#chatbot .overflow-y-auto{height:600px}
#send {background-color: #FFE7CF}
"""

default_chat_value = [
    None,
    "Hello, I'm a conversational travel assistant."
]


def user(user_message, history):
    return "", history + [[user_message, None]], history + [[user_message, None]]


def run_gradio(bot):
    with gr.Blocks(css=css, elem_id="chatbot") as demo:
        with gr.Row(visible=True) as btn_raws:
            with gr.Column(scale=5):
                style = gr.Radio(
                    ["concise", "detailed"], value=getattr(bot, 'reply_style', 'concise'), label="Reply Style"
                )

        chatbot = gr.Chatbot(
            elem_id="chatbot", label="Agent"
        )
        state = gr.State([])  # history
        with gr.Row(visible=True) as input_raws:
            with gr.Column(scale=4):
                txt = gr.Textbox(
                    show_label=False, placeholder="Enter text and press enter.", container=False
                )  # user_message
            with gr.Column(scale=1, min_width=0):
                send = gr.Button(value="Send", elem_id="send", variant="primary")
            with gr.Column(scale=1, min_width=0):
                clear = gr.Button(value="Clear")
        state.value = [default_chat_value]
        chatbot.value = [default_chat_value]

        txt.submit(user, [txt, state], [txt, state, chatbot]).then(
            bot.run_gr, [state], [chatbot, state]
        )
        txt.submit(lambda: "", None, txt)

        send.click(user, [txt, state], [txt, state, chatbot]).then(
            bot.run_gr, [state], [chatbot, state]
        )
        send.click(lambda: "", None, txt)
        style.change(bot.set_style, [style], None)

        clear.click(bot.clear)
        clear.click(lambda: [default_chat_value], None, chatbot)
        clear.click(lambda: [default_chat_value], None, state)

    demo.launch(share=False)
