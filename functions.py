def uploadImage(imageUrl):
    import requests
    from PIL import Image
    from io import BytesIO

    import pysftp

    response = requests.get(imageUrl, stream=True)

    image = Image.open(BytesIO(response.content))
    image = image.convert("RGB")
    return image


def ProcessImage(image):
    from PIL import Image

    # Determine the new size of the square image
    max_size = max(image.size[0], image.size[1])
    square_size = (max_size, max_size)

    # Create a new square image with a white background
    square_image = Image.new("RGB", square_size, (255, 255, 255))

    # Determine the offset to place the original image in the center of the square image
    x_offset = int((square_size[0] - image.size[0]) / 2)
    y_offset = int((square_size[1] - image.size[1]) / 2)

    # Paste the original image into the center of the square image
    square_image.paste(image, (x_offset, y_offset))

    # Resize the square image to be 1200 x 1200
    image_resized = square_image.resize((1200, 1200))
    return image_resized


def serverUpload(resizedImage, imageName):
    import pysftp
    import credentials
    from datetime import datetime
    from io import BytesIO

    hostname = credentials.hostname
    username = credentials.username
    password = credentials.password

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    folder_name = datetime.today().strftime("%Y-%m-%d")
    server_path = f"public_html/media/L9/{folder_name}/{imageName}"
    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            with sftp.cd("public_html/media/L9/"):
                if sftp.exists(folder_name):
                    pass
                else:
                    # create new directory at public_html/media/L9/ with the folder_name variable
                    sftp.mkdir(folder_name)

        # Save the resized image to a file-like object
        image_io = BytesIO()
        resizedImage.save(image_io, format="JPEG")

        # Upload the image to the server
        image_io.seek(0)  # Reset the file pointer to the beginning
        sftp.putfo(image_io, server_path)

        # close connection
        sftp.close()
    except Exception as e:
        print(f"Error: {str(e)}")


def removeBackground(url, imageName):
    import credentials
    import pysftp
    import requests
    from PIL import Image, ImageOps
    from io import BytesIO
    from datetime import datetime
    import rembg

    # set up variables to create file names and connect to server
    image_url = url
    imageName = imageName

    hostname = credentials.hostname
    username = credentials.username
    password = credentials.password

    folder_name = datetime.today().strftime("%Y-%m-%d")
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    server_path = f"public_html/media/L9/{folder_name}/{imageName}.jpg"
    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            with sftp.cd("public_html/media/L9/"):
                if sftp.exists(folder_name):
                    pass
                else:
                    # create new directory at public_html/media/L9/ with the folder_name variable
                    sftp.mkdir(folder_name)
            try:
                # open the image from the url
                response = requests.get(image_url, stream=True)
                # convert the image to a PIL image
                image = Image.open(BytesIO(response.content))

                # remove background from image
                image = rembg.remove(image)

                # creates a file like object to save the image to
                image_io = BytesIO()
                # saves the image with no background as a png
                image.save(image_io, format="PNG")

                # open it again with PIL so we can process it
                image2 = Image.open(image_io)
                h, w = image2.size
                if h > w:
                    imageSize = (h, h)
                else:
                    imageSize = (w, w)

                # Create a new square image with a white background
                square_image = Image.new("RGBA", (imageSize), (255, 255, 255, 0))

                # Calculate the position to center the original image on the new canvas
                position = (
                    (square_image.width - image2.width) // 2,
                    (square_image.height - image2.height) // 2,
                )

                # Paste the original image into the center of the square image
                square_image.paste(image2, position, image2)

                # convert the image to RGB
                square_image = square_image.convert("RGB")

                square_image = square_image.resize((1200, 1200))

                image_io2 = BytesIO()
                # Save the resized image to a file-like object
                square_image.save(image_io2, format="JPEG")

                # Upload the image to the server
                image_io2.seek(0)  # Reset the file pointer to the beginning
                sftp.putfo(image_io2, server_path)

                # close connection
                sftp.close()

                # creates a variable to pass to the html page to display the image and url
                BikeWagonUrl = (
                    f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"
                )
                return BikeWagonUrl
            except Exception as e:
                print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")


def CreateDict(df):
    import pandas as pd

    uniqueSku = df["SKU"].unique()

    # create a new df that will be a flattened version of the original df each sku will show up once
    newDf = pd.DataFrame()
    for sku in uniqueSku:
        filteredDf = df[df["SKU"] == sku]

        if len(filteredDf) > 1:
            for x in range(len(filteredDf)):
                # if it is the second or third images we add it as a new column to the sku
                if x != 0:
                    filteredDf[f"Image Title {x}"] = filteredDf.iloc[x]["Image Title"]
                    filteredDf[f"Image Url {x}"] = filteredDf.iloc[x]["Image Url"]
                    filteredDf[f"Server URL {x}"] = filteredDf.iloc[x]["Server URL"]

        # drop all rows except the first one that has all the images linked to it
        filteredDf = filteredDf.iloc[0]

        newDf = pd.concat([newDf, filteredDf], axis=1)
    newDf = newDf.T
    # newDf = newDf.drop("Image Url", axis=1)

    newDf = newDf.fillna("")
    # create a dictionary to pass to the view rather than passing the uniqe url and imageNames
    newDf.sort_values(by=["SKU"], inplace=True)
    dict = newDf.set_index("SKU").T.to_dict("list")

    for sku in dict:
        list = dict[sku]
        dictionary = {}
        keyList = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
        for i in range(len(list)):
            if list[i] != "":
                if i in keyList:
                    dictionary[list[i]] = []

                elif i < 3:
                    dictionary[list[0]].append(list[i])
                elif i < 6:
                    dictionary[list[3]].append(list[i])
                elif i < 9:
                    dictionary[list[6]].append(list[i])
                elif i < 12:
                    dictionary[list[9]].append(list[i])
                elif i < 15:
                    dictionary[list[12]].append(list[i])
                elif i < 18:
                    dictionary[list[15]].append(list[i])
                elif i < 21:
                    dictionary[list[18]].append(list[i])
                elif i < 24:
                    dictionary[list[21]].append(list[i])
                elif i < 27:
                    dictionary[list[24]].append(list[i])
                else:
                    dictionary[list[27]].append(list[i])

        dict[sku] = dictionary
    return dict


def is_png_transparent(image_path):
    from PIL import Image

    if image_path.startswith("http"):
        import requests
        from io import BytesIO

        response = requests.get(image_path, stream=True)
        image = Image.open(BytesIO(response.content))

    else:
        # Open the image file
        image = Image.open(image_path)

    # Check if the image has an alpha channel
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        # Get the pixel data
        pixel_data = image.load()

        # Iterate over each pixel and check the alpha value
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                # Check if the pixel is transparent
                if pixel_data[x, y][3] < 255:
                    return True

    return False


def checkForTransparency(url):
    import requests
    from PIL import Image
    from io import BytesIO
    import numpy as np

    try:
        # open the image from the url
        response = requests.get(url, stream=True)

        # convert the image to a PIL image
        image = Image.open(BytesIO(response.content))
        image = np.array(image)
        h, w, c = image.shape
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

    return True if c == 4 else False


def remove_after_second_space(text):
    words = text.split(" ")
    modified_string = " ".join(words[:2])
    return modified_string


def process_image(image):
    from PIL import Image
    from io import BytesIO

    # Determine the new size of the square image
    max_size = max(image.size[0], image.size[1])
    square_size = (max_size, max_size)

    # Create a new square image with a white background
    square_image = Image.new("RGBA", square_size, (255, 255, 255))

    # Determine the offset to place the original image in the center of the square image
    x_offset = int((square_size[0] - image.size[0]) / 2)
    y_offset = int((square_size[1] - image.size[1]) / 2)

    try:
        # Paste the original image into the center of the square image
        square_image.paste(image, (x_offset, y_offset), image)
    except Exception as e:
        print(e)
    # Resize the square image to be 1200 x 1200
    image_resized = square_image.resize((1200, 1200))

    # Save the resized image to a file-like object
    image_io = BytesIO()
    image_resized.convert("RGB").save(image_io, "JPEG")

    # Upload the image to the server
    image_io.seek(0)  # Reset the file pointer to the beginning

    return image_io
