from research_assistant.graph import agent
from io import BytesIO
from PIL import Image

png_bytes = agent.get_graph().draw_mermaid_png()
img = Image.open(BytesIO(png_bytes))
img.show()