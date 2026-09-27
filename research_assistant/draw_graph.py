from research_assistant.graph import build_agent
from io import BytesIO
from PIL import Image

png_bytes = build_agent().get_graph().draw_mermaid_png()
img = Image.open(BytesIO(png_bytes))
img.show()