from html2image import Html2Image
import os

hti = Html2Image(size=(1200, 800))

html_path = r"C:\Users\NIMISH PARDHI\.gemini\antigravity\brain\c7c4782c-1292-4db3-abb9-621a72c1c9bd\interactive_architecture.html"

# Check if the file exists
if os.path.exists(html_path):
    print("HTML file found. Capturing image...")
    # Capture the image
    hti.screenshot(html_file=html_path, save_as='architecture_diagram.png')
    print("Screenshot saved as architecture_diagram.png")
else:
    print(f"Error: Could not find HTML file at {html_path}")
