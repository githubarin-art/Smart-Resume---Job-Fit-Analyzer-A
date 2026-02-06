from reportlab.pdfgen import canvas

def create_resume():
    c = canvas.Canvas("test_resume.pdf")
    c.drawString(100, 800, "Anurag Mishra")
    c.drawString(100, 780, "Software Engineer")
    c.drawString(100, 760, "Skills: Python, React, FastAPI, SQL, AWS, Docker")
    c.drawString(100, 740, "Experience:")
    c.drawString(100, 720, "- Senior Engineer at Tech Corp (2020-Present): Built scalable APIs using FastAPI and Python.")
    c.drawString(100, 700, "- Developer at Startup Inc (2018-2020): Frontend development with React and Redux.")
    c.drawString(100, 680, "Education:")
    c.drawString(100, 660, "- B.Tech in Computer Science, 2018")
    c.save()
    print("Created test_resume.pdf")

if __name__ == "__main__":
    create_resume()
