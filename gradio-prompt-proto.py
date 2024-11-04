import gradio as gr

def chat(query):
    return "Hello! How can I help you today?"

ui = gr.Interface(fn=chat, inputs="text", outputs="text", title="Quectonic Prototype")

ui.launch()