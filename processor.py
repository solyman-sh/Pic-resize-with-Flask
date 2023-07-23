from PIL import Image


def processor(filename):
    file = './static/process/' + filename
    img = Image.open(file)
    grey = img.convert('L')
    grey.save(file)
